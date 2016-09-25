from PIL.Image import BILINEAR


LENGTH = 200
BLEED_PX = LENGTH * 0.07


# WISHLIST persist this somewhere
CACHE = {}


def expand(bbox, amount):
    """
    Expand a bounding box by `amount` pixels.
    """
    return (bbox[0] - amount, bbox[1] - amount, bbox[2] + amount, bbox[3] + amount)


def crop_1(im):
    """
    Crop buttons based on Pillow's built in .getbbox
    """
    # Square off the image since the left and right edges are meaningless
    trim_l = (im.width - im.height) // 2
    square = im.crop(expand(
        (trim_l, 0, trim_l + im.height, im.height),
        -int(im.height * 0.10)  # Trim around the edges
    ))

    bbox = CACHE.get(im.filename)
    if not bbox:
        # TODO smarter downsampling
        copy = square.copy()
        copy.thumbnail((LENGTH, LENGTH), BILINEAR)

        ratio = square.width / copy.width

        gray = copy.convert('L')

        # Pre-process mask
        bw = gray.point(lambda x: 0 if 190 < x else 255, '1')
        # treat highlights as features
        # bw = gray.point(lambda x: 0 if 190 < x > 250 else 255, '1')
        bbox = bw.getbbox()

        # return bw.crop(box=bbox)  # DEBUG: to evaluate quality of the crop
        # TODO make sure box is square-ish
        left, top, right, bottom = expand(bbox, BLEED_PX)
        bbox = (
            max(0, left * ratio),
            max(0, top * ratio),
            min(square.width, right * ratio),
            min(square.height, bottom * ratio),
        )
        CACHE[im.filename] = bbox

    return square.crop(box=bbox)
