import argparse
import asyncio
import json
import logging
import os.path
import shutil
from collections import namedtuple
from glob import glob
from io import BytesIO
from urllib.parse import quote

import aiohttp_jinja2
import aioredis
import jinja2
from aioauth_client import GoogleClient
from aiohttp import web
from aiohttp_session import setup as setup_session, get_session
from aiohttp_session.redis_storage import RedisStorage
from PIL import Image
from pyexiv2 import ImageMetadata
from natsort import natsorted


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)


# MODELS
########

Dimensions = namedtuple('Dimensions', ['width', 'height'])


class Item():
    """
    An image in your storage.

    Called `Item` to avoid clashing with PIL's `Image`.
    """
    # IPTC values:
    #   http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/IPTC.html
    # Based on:
    #   https://www.flickr.com/groups/51035612836@N01/discuss/72057594065133113/
    # Useful tags are: Caption-Abstract, ObjectName == Headline, Keywords
    FORM = (
        'Iptc.Application2.Headline',
        'Iptc.Application2.Caption',
        # 'Iptc.Application2.Keywords',  # TODO
    )

    """A gallery item."""
    def __init__(self, path):
        self.path = path
        self.abspath = args.STORAGE_DIR + path  # why does os.path.join not work?
        self.meta = ImageMetadata(self.abspath)
        self.meta.read()
        im = Image.open(self.abspath)
        self.dimensions = Dimensions(*im.size)
        self.filesize = os.path.getsize(self.abspath)

    def __str__(self):
        return os.path.basename(self.path)

    @property
    def src(self):
        """Get the html 'src' attributes."""
        thumb_path = '/thumbs' + self.path if self.filesize > 30000 else '/images' + self.path
        return {
            'thumb': quote(thumb_path),
            'original': quote('/images' + self.path),
        }

    @property
    def backup_abspath(self):
        """
        The absolute path to where the backup for this image should go.

        In the future we may a new setting so originals aren't cluttering the
        storage directory.
        """
        return self.abspath + '.original'

    def get_safe_value(self, meta, key):
        """
        Get the meta value or an empty string.

        http://python3-exiv2.readthedocs.io/en/latest/api.html
        http://python3-exiv2.readthedocs.io/en/latest/tutorial.html
        """
        try:
            val = meta[key].value
            if meta[key].repeatable:
                return val

            return val[0]

        except UnicodeDecodeError:
            logger.warn('%s could not get meta for %s', self, key)
            return ''

    def get_all_meta(self):
        """Dict of meta tags were used in a human-readable format."""
        return {key: self.get_safe_value(self.meta, key) for key in self.meta.iptc_keys}

    def get_form_fields(self):
        ret = []
        for field in self.FORM:
            if field in self.meta.iptc_keys:
                ret.append((field, self.get_safe_value(self.meta, field)))
            else:
                ret.append((field, ''))
        return ret


# HANDLERS/VIEWS
################

@aiohttp_jinja2.template('index.html')
async def homepage(request):
    session = await get_session(request)

    # TODO get *.jpeg too
    images = natsorted(
        glob(os.path.join(args.STORAGE_DIR, '**/*.jpg'), recursive=True),
        key=lambda x: x.upper(),
    )

    return {
        'title': os.path.basename(args.STORAGE_DIR) or 'Gallery CMS',
        'images': (Item(x.replace(args.STORAGE_DIR, '')) for x in images),
        'is_authed': session.get('is_authed'),
        'session': session,
    }


async def thumbs(request):
    path = '/' + request.match_info['image']
    thumb_dimension = 256, 256  # TODO extract this from the request
    abspath = args.STORAGE_DIR + path
    im = Image.open(abspath)
    im.thumbnail(thumb_dimension)
    bytes_file = BytesIO()
    im.save(bytes_file, 'jpeg')
    return web.Response(
        status=200, body=bytes_file.getvalue(), content_type='image/jpeg',
        headers={
            'Cache-Control': 'max-age=86400',
        })


async def save(request):
    # session = await get_session(request)

    # TODO csrf
    data = await request.post()
    item = Item(data['src'])

    # Update name
    new_src = data.get('new_src')
    if new_src:
        new_abspath = os.path.abspath(args.STORAGE_DIR + new_src)
        if not new_abspath.startswith(args.STORAGE_DIR):
            return web.Response(status=400, body=b'Invalid Request')

        if new_abspath != item.abspath:
            if os.path.isfile(new_abspath):
                return web.Response(
                    status=400,
                    body='{} Already Exists'.format(new_src).encode('utf8'),
                )

            shutil.move(item.abspath, new_abspath)
            old_backup_abspath = item.backup_abspath
            item = Item(new_src)
            if os.path.isfile(old_backup_abspath):
                shutil.move(old_backup_abspath, item.backup_abspath)

    # Update meta
    for field in item.FORM:
        # TODO handle .repeatable (keywords)
        item.meta[field] = [data.get(field, '')]

    if args.save_originals and not os.path.isfile(item.backup_abspath):
        shutil.copyfile(item.abspath, item.backup_abspath)

    # WISHLIST don't write() if nothing changed
    item.meta.write()

    response_data = dict(item.get_form_fields(), src=new_src)
    return web.Response(
        status=200,
        body=json.dumps(response_data).encode('utf8'),
        content_type='application/json',
        headers={
            # Let fallback saves go back to the homepage w/o AJAX.
            # `Refresh` is not an official HTTP header.
            'Refresh': '3; url={}://{}/'.format(request.scheme, request.host),
        },
    )


async def login(request):
    session = await get_session(request)

    client = GoogleClient(
        client_id=os.getenv('OAUTH_CLIENT_ID'),
        client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
        scope='email profile',
    )
    client.params['redirect_uri'] = '{}://{}{}'.format(request.scheme, request.host, request.path)

    if client.shared_key not in request.GET:  # 'code' not in request.GET
        return web.HTTPFound(client.get_authorize_url())

    access_token, __ = await client.get_access_token(request.GET)
    user, info = await client.user_info()
    # TODO store in session storage

    if user.email in args.admins:
        session['is_authed'] = True
        session['user'] = {
            'name': info['displayName'],
            'email': user.email,
            'avatar': user.picture,
        }
    else:
        return web.HTTPForbidden()

    return web.HTTPFound('/')


async def logout(request):
    session = await get_session(request)
    session['is_authed'] = False
    return web.HTTPFound('/')


# HELPERS
#########

def create_app(loop=None):
    app = web.Application()
    app.router.add_static('/images', args.STORAGE_DIR)
    app.router.add_static('/static', os.path.join(BASE_DIR, 'app'))
    app.router.add_route('GET', '/', homepage)
    app.router.add_route('GET', '/thumbs/{image}', thumbs)
    app.router.add_route('POST', '/save/', save)
    app.router.add_route('GET', '/login/', login)
    app.router.add_route('GET', '/logout/', logout)
    return app


async def connect_to_redis(loop):
    redis_pool = await aioredis.create_pool(
        ('localhost', 6379),  # TODO
        loop=loop)
    return redis_pool


def dir_w_ok(user_dir):
    user_dir = os.path.abspath(user_dir)

    if not os.access(user_dir, os.W_OK):
        raise argparse.ArgumentTypeError("Directory is not writeable")

    return user_dir


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '--port', type=int, default=os.environ.get('PORT', 8080),
        help='Port to listen on [default: 8080]')
    parser.add_argument(
        '--no-save-originals', dest='save_originals', action='store_false',
        help='Save original files [default: True]')
    parser.add_argument(
        'STORAGE_DIR', type=dir_w_ok,
        help='Directory to serve images from')
    parser.add_argument(
        '--admin', metavar='EMAIL', action='append', dest='admins',
        help='Google emails to give admin access')
    args = parser.parse_args()

    app = create_app()

    loop = asyncio.get_event_loop()
    redis_pool = loop.run_until_complete(connect_to_redis(loop))
    setup_session(app, RedisStorage(
        redis_pool,
        cookie_name='gallery-cms-dev:1',
    ))

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
    )
    web.run_app(app, port=args.port)
