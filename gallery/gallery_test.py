import os
from unittest.mock import patch

from aiohttp.test_utils import make_mocked_request
from multidict import MultiDict

from .gallery import save, settings


BASE_DIR = os.path.abspath(os.path.join('..', os.path.dirname(__file__)))
pytest_plugins = 'aiohttp.pytest_plugin'


async def test_handler_save(test_client):
    async def post():
        return MultiDict({
            'Headline': '',
            'Caption-Abstract': '',
            'src': '/Lenna.jpg',
            'Keywords': ''
        })

    req = make_mocked_request('post', '/foo/')
    req.post = post

    with patch.object(settings, 'STORAGE_DIR', new=os.path.join(BASE_DIR, 'fixtures')):
        resp = await save(req)

    print(resp.body)
    1/0
