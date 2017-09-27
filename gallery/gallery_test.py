import argparse
import os
import random
import shutil
from unittest.mock import patch, MagicMock

import pytest
from aiohttp.test_utils import make_mocked_request
from multidict import MultiDict

from .gallery import (
    CIPHER_KEY,
    encode, decode, thumbs, save, login, Item,
    get_redis_info, dir_w_ok,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(BASE_DIR, 'fixtures/')
pytest_plugins = 'aiohttp.pytest_plugin'


class AsyncMock(MagicMock):
    """
    MagicMock, but for async

    Fixes "TypeError: object MagicMock can't be used in 'await' expression"

    http://stackoverflow.com/questions/32480108/mocking-async-call-in-python-3-5/32498408#32498408
    """
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


# FIXTURES
##########

@pytest.fixture
def jpeg(request):
    """Make a temp JPEG. Returns the path relative to FIXTURES_DIR."""
    def fin():
        try:
            os.unlink(os.path.join(FIXTURES_DIR, 'tmpLenna.jpg'))
            os.unlink(os.path.join(FIXTURES_DIR, 'tmpLenna.jpg.original'))
        except FileNotFoundError:
            pass

    shutil.copyfile(os.path.join(FIXTURES_DIR, 'Lenna.jpg'),
                    os.path.join(FIXTURES_DIR, 'tmpLenna.jpg'))
    request.addfinalizer(fin)
    return 'tmpLenna.jpg'


# TESTS
#######

def test_encode_decode():
    encoded = encode('key', 'metal idol')
    assert encoded == 'w5jDisOtw4zDkcKZw5TDicOow5c='
    assert decode('key', encoded) == 'metal idol'


async def test_item():
    with patch('gallery.gallery.args', STORAGE_DIR=FIXTURES_DIR, create=True):
        item = Item('/Lenna.jpg')

    assert str(item) == 'Lenna.jpg'
    assert item.src['original'] == '/images/Lenna.jpg'
    assert item.get_safe_value('nonexistent tag') == ''


async def test_handler_thumbs_404s_for_bad_requests():
    req = MagicMock(match_info={'encoded': 'gibberish'})

    with patch('gallery.gallery.args', STORAGE_DIR=FIXTURES_DIR, cache='/tmp', create=True):
        resp = await thumbs(req)
        assert resp.status == 404

        # A directory instead of an image
        req.match_info = {'encoded': encode(CIPHER_KEY, '1x1:/')}
        resp = await thumbs(req)
        assert resp.status == 404

        # Missing file
        req.match_info = {'encoded': encode(CIPHER_KEY, '1x1:/haha.jpg')}
        resp = await thumbs(req)
        assert resp.status == 404


async def test_handler_thumbs_delivers_jpeg():
    req = MagicMock(match_info={'encoded': encode(CIPHER_KEY, 'v1:1x1:/Lenna.jpg')})
    with patch('gallery.gallery.args', STORAGE_DIR=FIXTURES_DIR, cache='/tmp', create=True):
        resp = await thumbs(req)
    assert resp.status == 200
    assert resp.headers['content-type'] == 'image/jpeg'


async def test_handler_save(jpeg):
    headline = 'headline {}'.format(random.randint(0, 99))
    caption = 'caption {}'.format(random.randint(0, 99))

    async def post():
        return MultiDict({
            'src': jpeg,
            'Iptc.Application2.Headline': headline,
            'Iptc.Application2.Caption': caption,
            'Iptc.Application2.Keywords': 'test keyword',
        })

    req = make_mocked_request('post', '/foo/')
    req.post = post

    with patch('gallery.gallery.args', STORAGE_DIR=FIXTURES_DIR, create=True):
        resp = await save(req)

        assert resp.status == 200

        item = Item(jpeg)
        assert item.meta['Iptc.Application2.Headline'].value == [headline]
        assert item.meta['Iptc.Application2.Caption'].value == [caption]
        assert item.meta['Iptc.Application2.Keywords'].value == ['test keyword']

        assert os.path.isfile(item.backup_abspath)


async def test_handler_save_can_rename(jpeg):
    async def post():
        return MultiDict({
            'src': jpeg,
            'new_src': '/tmpDeleteme.jpg',
        })

    req = make_mocked_request('post', '/foo/')
    req.post = post

    with patch('gallery.gallery.args', STORAGE_DIR=FIXTURES_DIR, create=True):
        resp = await save(req)

        assert resp.status == 200

        item = Item('/tmpDeleteme.jpg')

        assert os.path.isfile(item.abspath)
        os.unlink(item.abspath)
        assert os.path.isfile(item.backup_abspath)
        os.unlink(item.backup_abspath)


async def test_handler_save_errors_with_invalid_name(jpeg):
    async def post():
        return MultiDict({
            'src': jpeg,
            'new_src': '/../tmpDeleteme.jpg',
        })

    req = make_mocked_request('post', '/foo/')
    req.post = post

    with patch('gallery.gallery.args', STORAGE_DIR=FIXTURES_DIR, create=True):
        resp = await save(req)

        assert resp.status == 400
        assert b'Invalid' in resp.body


async def test_handler_save_errors_with_existing_name(jpeg):
    async def post():
        return MultiDict({
            'src': jpeg,
            'new_src': '/existing.jpg',
        })

    req = make_mocked_request('post', '/foo/')
    req.post = post

    with patch('gallery.gallery.args', STORAGE_DIR=FIXTURES_DIR, create=True):
        resp = await save(req)

        assert resp.status == 400
        assert b'Already Exists' in resp.body


async def test_handler_login_redirects():
    req = make_mocked_request('get', '/login/')

    with patch('gallery.gallery.get_session', new=AsyncMock()):
        resp = await login(req)

    assert resp.status == 302
    assert 'https://accounts.google.com/o/oauth2/auth' in resp.location


def test_get_redis_info():
    assert get_redis_info('redis://localhost:6379') == ('localhost', 6379)
    assert get_redis_info('redis://redis:999') == ('redis', 999)
    assert get_redis_info('redis://redis') == ('redis', 6379)


async def test_dir_w_ok():
    assert dir_w_ok('.')

    with pytest.raises(argparse.ArgumentTypeError):
        dir_w_ok('/tmp/%s' % random.randint(100, 999))
