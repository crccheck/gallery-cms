import json
import logging
import os.path
from glob import glob
from urllib.parse import quote

import aiohttp_jinja2
import jinja2
from aiohttp import web
# from PIL import Image
from pyexiv2 import ImageMetadata

# from gallery import settings
import settings


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)


class Item():
    # IPTC values:
    #   http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/IPTC.html
    # Based on:
    #   https://www.flickr.com/groups/51035612836@N01/discuss/72057594065133113/
    # Useful tags are: Caption-Abstract, ObjectName == Headline, Keywords
    FORM = (
        'Iptc.Application2.Headline',
        'Iptc.Application2.Caption',
        'Iptc.Application2.Keywords',
    )

    """A gallery item."""
    def __init__(self, path):
        self.path = path
        abspath = settings.STORAGE_DIR + path  # why does os.path.join not work?
        self.meta = ImageMetadata(abspath)
        self.meta.read()

    def __str__(self):
        return os.path.basename(self.path)

    @property
    def src(self):
        """Get the html 'src' attribute."""
        return quote(self.path)

    @property
    def keywords(self):
        return self.meta.get('Iptc.Application2.Keywords').value

    @property
    def headline(self):
        return self.meta.get('Iptc.Application2.Headline').value

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

    def get_meta_used(self):
        """List what meta tags were used in a human-readable format."""
        return self.meta.iptc_keys

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


@aiohttp_jinja2.template('index.html')
async def homepage(request):
    # TODO get *.jpeg too
    images = glob(os.path.join(settings.STORAGE_DIR, '**/*.jpg'), recursive=True)
    return {'images': (Item(x.replace(settings.STORAGE_DIR, '')) for x in images)}


async def save(request):
    # TODO csrf
    data = await request.post()

    item = Item(data['src'])
    print('meta', item.get_all_meta())
    # http://pillow.readthedocs.io/en/latest/handbook/image-file-formats.html#jpeg
    # im.save('test.jpg', 'JPEG', exif=exit)

    return web.Response(
        status=200,
        body=json.dumps(dict(data)).encode('utf8'),
        content_type='application/json',
    )


def create_app(loop=None):
    if loop is None:
        app = web.Application()
    else:
        app = web.Application(loop=loop)
    app.router.add_static('/images', settings.STORAGE_DIR)
    app.router.add_route('GET', '/', homepage)
    app.router.add_route('POST', '/save/', save)
    return app


if __name__ == '__main__':
    app = create_app()
    print(BASE_DIR, os.path.join(BASE_DIR, 'templates'))
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
    )
    web.run_app(app)
