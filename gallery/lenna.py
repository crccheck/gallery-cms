from pprint import pprint

from PIL import Image, IptcImagePlugin
from pyexiv2 import ImageMetadata


im = Image.open('fixtures/Lenna.jpg')
meta = IptcImagePlugin.getiptcinfo(im)
pprint(meta)


meta2 = ImageMetadata('fixtures/Lenna.jpg')
meta2.read()
for key in meta2.iptc_keys:
    val = meta2[key]
    print('=' * 80)
    print(val)
    print(val.title, '/', val.name, '/', val.photoshop_name)
    print(val.description)
    print(val.key)
    print(val.repeatable, val.value)
