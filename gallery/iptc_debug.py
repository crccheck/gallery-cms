"""
Peek at what IPTC info other programs add to files
"""
import sys

from pprint import pprint


def pil(file_path: str):
    from PIL import Image, IptcImagePlugin

    im = Image.open(file_path)
    meta = IptcImagePlugin.getiptcinfo(im)
    pprint(meta)


def iptcinfo(file_path: str):
    from iptcinfo3 import IPTCInfo, c_datasets_r

    info = IPTCInfo(file_path, inp_charset="utf_8")
    # print(info.values())
    for k, v in c_datasets_r.items():
        # print(f"{k}\t{v}")
        iptc_value = info[k]
        if iptc_value:
            print(f"{v}\t{k}\t{iptc_value}")


def xmp(file_path: str):
    from libxmp.utils import file_to_dict
    from libxmp.consts import XMP_NS_XMP

    xmp = file_to_dict(file_path)
    for key, value, options in xmp[XMP_NS_XMP]:
        print(key, value)


if __name__ == "__main__":
    iptcinfo(sys.argv[1])
    pil(sys.argv[1])
    xmp(sys.argv[1])
