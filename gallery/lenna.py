from PIL import Image, IptcImagePlugin


im = Image.open('/home/crc/Dropbox/Lenna.jpg')
meta = IptcImagePlugin.getiptcinfo(im)
print(meta)
