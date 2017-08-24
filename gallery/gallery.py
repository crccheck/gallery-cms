# -*- coding: UTF-8 -*-
import argparse
import asyncio
import base64
import binascii
import json
import logging
import logging.config
import os
import re
import shutil
from collections import namedtuple
from glob import iglob
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

from crop import crop_1


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIPHER_KEY = os.getenv('CIPHER_KEY', 'roflcopter')
jpeg_matcher = re.compile(r'.+\.jpe?g$', re.IGNORECASE)
logger = logging.getLogger(__name__)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': os.getenv('LOGGING_LEVEL', 'DEBUG'),
            'class': 'project_runpy.ColorizingStreamHandler',
            'formatter': 'main',
        },
    },
    'formatters': {
        'main': {
            # Docs:
            # https://docs.python.org/3/library/logging.html#logrecord-attributes
            'format': '[%(name)s] %(message)s',
        },
    },
    'loggers': {
        '': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'aiohttp.access': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        }
    },
})


# UTILS
#######

def encode(key, string):
    """
    Vigenère cipher encode.

    Makes sure the url is safe.
    Just a simple obfuscation using only the standard lib.
    http://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password/2490718#2490718
    """
    encoded_chars = []
    for idx, char in enumerate(string):
        key_c = key[idx % len(key)]
        encoded_c = chr(ord(char) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = ''.join(encoded_chars)
    return base64.urlsafe_b64encode(encoded_string.encode('utf8')).decode('utf8')


def decode(key, string):
    string = base64.urlsafe_b64decode(string).decode('utf8')
    encoded_chars = []
    for idx, char in enumerate(string):
        key_c = key[idx % len(key)]
        encoded_c = chr(ord(char) - ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = ''.join(encoded_chars)
    return encoded_string


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
        return {
            'thumb': quote('/thumbs/' + encode(CIPHER_KEY, 'v1:300x300:' + self.path)),
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

    def get_safe_value(self, key):
        """
        Get the meta value or an empty string.

        http://python3-exiv2.readthedocs.io/en/latest/api.html
        http://python3-exiv2.readthedocs.io/en/latest/tutorial.html
        """
        try:
            val = self.meta[key].value
            if self.meta[key].repeatable:
                return val

            return val[0]

        except KeyError:
            return ''

    def get_form_fields(self):
        ret = {
            'Iptc.Application2.Headline':
                self.get_safe_value('Iptc.Application2.Headline'),
            'Iptc.Application2.Caption':
                self.get_safe_value('Iptc.Application2.Caption'),
            'Iptc.Application2.Keywords':
                self.get_safe_value('Iptc.Application2.Keywords'),
        }
        return ret


# HANDLERS/VIEWS
################

@aiohttp_jinja2.template('index.html')
async def homepage(request):
    session = await get_session(request)
    all_files = iglob(os.path.join(args.STORAGE_DIR, '**/*'), recursive=True)
    all_jpegs = (x for x in all_files if jpeg_matcher.search(x))
    all_items = (Item(x.replace(args.STORAGE_DIR, '')) for x in all_jpegs)
    all_images = natsorted(
        all_items,
        key=lambda x: (x.get_safe_value('Iptc.Application2.Headline') or str(x)).upper(),
    )

    return {
        'title': os.path.basename(args.STORAGE_DIR) or 'Gallery CMS',
        'images': all_images,
        'is_authed': session.get('is_authed'),
        'session': session,
    }


async def thumbs(request, crop=True):
    encoded = request.match_info['encoded']
    try:
        __, w_x_h, path = decode(CIPHER_KEY, encoded).split(':', 3)
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return web.HTTPNotFound()

    # WISHLIST add as extra context to the aiohttp.access logger
    logger.info('Decoded as %s %s', path, w_x_h)
    abspath = args.STORAGE_DIR + path
    try:
        im = Image.open(abspath)
    except (FileNotFoundError, IsADirectoryError):
        return web.HTTPNotFound()

    thumb_dimension = [int(x) for x in w_x_h.split('x')]
    bytes_file = BytesIO()

    if crop:
        cropped_im = crop_1(im)
        cropped_im.thumbnail(thumb_dimension)
        cropped_im.save(bytes_file, 'jpeg')
    else:
        im.thumbnail(thumb_dimension)
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
    # XXX Must be kept up to date with Item.get_form_fields
    item.meta['Iptc.Application2.Headline'] = [data.get('Iptc.Application2.Headline', '')]
    item.meta['Iptc.Application2.Caption'] = [data.get('Iptc.Application2.Caption', '')]
    item.meta['Iptc.Application2.Keywords'] = data.getall('Iptc.Application2.Keywords', [])

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
    # FIXME not picking up https
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
    app.router.add_route('GET', '/thumbs/{encoded}', thumbs)
    # app.router.add_route('GET', '/thumbs/{dimensions}/{image}', thumbs)
    app.router.add_route('POST', '/save/', save)
    app.router.add_route('GET', '/login/', login)
    app.router.add_route('GET', '/logout/', logout)
    return app


def get_redis_info(url):
    match = re.match(r'redis://(?P<host>[^:]+)(:(?P<port>\d+))?', url)
    data = match.groupdict()
    return data['host'], int(data['port'] or 6379)


async def connect_to_redis(loop):
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_pool = await aioredis.create_pool(get_redis_info(redis_url), loop=loop)
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
