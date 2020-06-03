import os
from io import BytesIO
from itertools import islice
from pathlib import Path

from PIL import Image
from starlette.responses import Response, PlainTextResponse

# TODO centralize this
BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.abspath(__file__)))
THUMBNAIL_SIZE = (300, 300)
DEFAULT_SIZE = 200


def thumbs(request):
    # NOTE: PIL won't create a thumbnail larger than the original
    size = int(request.query_params.get("size", DEFAULT_SIZE))
    image_file = Path(BASE_DIR, request.path_params["path"])
    if not image_file.exists():
        return PlainTextResponse("Not found", status_code=404)

    im = Image.open(image_file)
    # TODO cache thumbnails
    im.thumbnail((size, size))
    fp = BytesIO()
    im.save(fp, format="webp")

    fp.seek(0)
    # WISHLIST support 304 not modified, etag, content-disposition
    # last_modified = image_file.stat().st_mtime
    # Last-Modified: Wed, 21 Oct 2015 07:28:00 GMT
    # last_modified_str = dt.datetime.fromtimestamp(last_modified).strftime(
    #     "%a, %e %b %Y %H:%M:%S"
    # )
    return Response(
        fp.read(),
        headers={
            "Cache-Control": f"public, max-age={86400 * 7}",
            # "Last-Modified": f"{last_modified_str} GMT",
        },
        media_type="image/webp",
    )


def album_thumb(request):
    size = int(request.query_params.get("size", DEFAULT_SIZE / 2))
    album_path = Path(BASE_DIR, request.path_params["path"])

    thumb = Image.new("RGB", (size, size))
    first_four_images = islice(album_path.glob("*.jpg"), 4)
    for idx, img_path in enumerate(first_four_images):
        im = Image.open(str(img_path))
        # TODO crop thumbnails to square before thumbnailing
        im.thumbnail((size / 2, size / 2))
        thumb.paste(im, (int(idx / 2) * int(size / 2), (idx % 2) * int(size / 2)))

    fp = BytesIO()
    thumb.save(fp, format="webp")

    fp.seek(0)
    return Response(
        fp.read(),
        headers={"Cache-Control": f"public, max-age=900"},
        media_type="image/webp",
    )
