import os
import random
import shutil
from unittest.mock import patch

import pytest
from aiohttp.test_utils import make_mocked_request
from multidict import MultiDict

from .gallery import save, settings, Item


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(BASE_DIR, 'fixtures/')
pytest_plugins = 'aiohttp.pytest_plugin'


@pytest.fixture
def jpeg(request):
    """Make a temp JPEG. Returns the path relative to FIXTURES_DIR."""
    def fin():
        try:
            os.unlink(os.path.join(FIXTURES_DIR, 'tmpLenna.jpg'))
            # XXX assumes SAVE_ORIGINALS == True
            os.unlink(os.path.join(FIXTURES_DIR, 'tmpLenna.jpg.original'))
        except FileNotFoundError:
            pass

    shutil.copyfile(os.path.join(FIXTURES_DIR, 'Lenna.jpg'),
                    os.path.join(FIXTURES_DIR, 'tmpLenna.jpg'))
    request.addfinalizer(fin)
    return 'tmpLenna.jpg'


async def test_handler_save(jpeg):
    headline = 'headline {}'.format(random.randint(0, 99))
    caption = 'caption {}'.format(random.randint(0, 99))

    async def post():
        return MultiDict({
            'src': jpeg,
            'Iptc.Application2.Headline': headline,
            'Iptc.Application2.Caption': caption,
        })

    req = make_mocked_request('post', '/foo/')
    req.post = post

    with patch.object(settings, 'STORAGE_DIR', new=FIXTURES_DIR):
        resp = await save(req)

        assert resp.status == 200

        item = Item(jpeg)
        assert item.meta['Iptc.Application2.Headline'].value == [headline]
        assert item.meta['Iptc.Application2.Caption'].value == [caption]

        # XXX assumes SAVE_ORIGINALS == True
        assert os.path.isfile(item.backup_abspath)


async def test_handler_save_can_rename(jpeg):
    async def post():
        return MultiDict({
            'src': jpeg,
            'new_src': '/tmpDeleteme.jpg',
        })

    req = make_mocked_request('post', '/foo/')
    req.post = post

    with patch.object(settings, 'STORAGE_DIR', new=FIXTURES_DIR):
        resp = await save(req)

        assert resp.status == 200

        item = Item('/tmpDeleteme.jpg')

        assert os.path.isfile(item.abspath)
        os.unlink(item.abspath)
        # XXX assumes SAVE_ORIGINALS == True
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

    with patch.object(settings, 'STORAGE_DIR', new=FIXTURES_DIR):
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

    with patch.object(settings, 'STORAGE_DIR', new=FIXTURES_DIR):
        resp = await save(req)

        assert resp.status == 400
        assert b'Already Exists' in resp.body
