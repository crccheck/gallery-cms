import os
from io import BytesIO
from pathlib import Path

from PIL import Image
from starlette.responses import Response, PlainTextResponse

# TODO centralize this
BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.abspath(__file__)))


def thumbs(request):
    image_file = Path(BASE_DIR, request.path_params["path"])
    if not image_file.exists():
        return PlainTextResponse("Not found", status_code=404)

    im = Image.open(image_file)
    # TODO multiple sizes
    # TODO cache thumbnails
    im.thumbnail((200, 200))
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
