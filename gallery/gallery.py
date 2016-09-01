import os.path
from glob import glob

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

    def __str__(self):
        return self.path


@aiohttp_jinja2.template('index.html')
async def homepage(request):
    images = glob(os.path.join(settings.STORAGE_DIR, '**/*.jpg'), recursive=True)

    return {'images': (Image(x) for x in images)}


if __name__ == '__main__':
    app = web.Application()
    app.router.add_route('GET', '/', homepage)
    app.router.add_static('/images', settings.STORAGE_DIR)

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
    )
    web.run_app(app)
