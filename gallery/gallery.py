import os.path
from glob import glob
from urllib.parse import quote

import aiohttp_jinja2
import jinja2
from aiohttp import web
# from PIL import Image, IptcImagePlugin

import settings


BASE_DIR = os.path.abspath(os.path.join('..', os.path.dirname(__file__)))
# im = Image.open('/home/crc/Dropbox/Lenna.jpg')
# exif = IptcImagePlugin.getiptcinfo(im)


class Image():
    def __init__(self, path):
        self.path = path

    @property
    def src(self):
        """Get the html 'src' attribute."""
        return quote(self.path)

    def __str__(self):
        return os.path.basename(self.path)


@aiohttp_jinja2.template('index.html')
async def homepage(request):
    # TODO get *.jpeg too
    images = glob(os.path.join(settings.STORAGE_DIR, '**/*.jpg'), recursive=True)

    return {'images': (Image(x.replace(settings.STORAGE_DIR, '')) for x in images)}


if __name__ == '__main__':
    app = web.Application()
    app.router.add_static('/images', settings.STORAGE_DIR)
    app.router.add_route('GET', '/', homepage)

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
    )
    web.run_app(app)
