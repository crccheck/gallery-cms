import os.path
from glob import glob
from urllib.parse import quote

import aiohttp_jinja2
import jinja2
from aiohttp import web
from PIL import Image, IptcImagePlugin

import settings


BASE_DIR = os.path.abspath(os.path.join('..', os.path.dirname(__file__)))


class Item():
    # http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/IPTC.html
    # TODO use some sort of model to validate these values
    NAME = {
        (2, 0): 'ApplicationRecordVersion',
        (2, 25): 'Keywords',
        (2, 40): 'SpecialInstructions',
        (2, 55): 'DateCreated',
        (2, 60): 'TimeCreated',
        (2, 80): 'Byline',
        (2, 90): 'City',
        (2, 95): 'Province-State',
        (2, 103): 'OriginalTransmissionReference',
        (2, 105): 'Headline',
        (2, 110): 'Credit',
        (2, 115): 'Source',
        (2, 120): 'Caption-Abstract',
    }

    """A gallery item."""
    def __init__(self, path):
        self.path = path
        abspath = settings.STORAGE_DIR + path  # why does os.path.join not work?
        self.im = Image.open(abspath)
        self.meta = IptcImagePlugin.getiptcinfo(self.im) or {}

    def __str__(self):
        return os.path.basename(self.path)

    @property
    def src(self):
        """Get the html 'src' attribute."""
        return quote(self.path)

    @property
    def keywords(self):
        return self.meta.get((2, 25))

    @property
    def headline(self):
        return self.meta.get((2, 105))

    def get_meta_used(self):
        """List what meta tags were used in a human-readable format."""
        return [self.NAME.get(x, x) for x in self.meta.keys()]

    def get_all_meta(self):
        """Dict of meta tags were used in a human-readable format."""
        return {self.NAME.get(k, k): v for k, v in self.meta.items()}


@aiohttp_jinja2.template('index.html')
async def homepage(request):
    # TODO get *.jpeg too
    images = glob(os.path.join(settings.STORAGE_DIR, '**/*.jpg'), recursive=True)
    return {'images': (Item(x.replace(settings.STORAGE_DIR, '')) for x in images)}


if __name__ == '__main__':
    app = web.Application()
    app.router.add_static('/images', settings.STORAGE_DIR)
    app.router.add_route('GET', '/', homepage)

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
    )
    web.run_app(app)
