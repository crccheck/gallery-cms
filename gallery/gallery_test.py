from aiohttp.test_utils import make_mocked_request
from multidict import MultiDict

from .gallery import save

pytest_plugins = 'aiohttp.pytest_plugin'


async def test_hello(test_client):
    async def post():
        return MultiDict({'a': 1})

    req = make_mocked_request('post', '/foo/')
    req.post = post

    resp = await save(req)

    print(resp.body)
    1/0
