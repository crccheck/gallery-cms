import os
from pathlib import Path
from textwrap import dedent

import graphene
import PIL
from graphene import relay
from iptcinfo3 import IPTCInfo
from libxmp import XMPFiles
from libxmp.consts import XMP_NS_XMP
from libxmp.utils import file_to_dict


BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.abspath(__file__)))


class ImageFileInfo(graphene.ObjectType):
    """
    meta information about the `Image` from the filesystem
    """

    path = graphene.String()
    size = graphene.Int()
    created = graphene.Int()
    modified = graphene.Int()
    accessed = graphene.Int()


class ImageAttributes(graphene.ObjectType):
    """
    meta information about the `Image` from PIL
    """

    format = graphene.String(required=True)
    mode = graphene.String(required=True)
    width = graphene.Int(required=True)
    height = graphene.Int(required=True)


class ImageIPTC(graphene.ObjectType):
    caption = graphene.String(description="caption/abstract")
    keywords = graphene.List(graphene.String, description="keywords")

    def resolve_caption(parent, info):
        return parent["caption/abstract"]

    def resolve_keywords(parent, info):
        return parent["keywords"]


class ImageXMP(graphene.ObjectType):
    rating = graphene.Int(
        required=True,
        default_value=0,
        description=dedent(
            """
        -1 == "rejected"
        0 == "unrated"
        1 to 5 == your rating
        https://iptc.org/std/photometadata/specification/IPTC-PhotoMetadata#image-rating
        """
        ),
    )

    def resolve_rating(parent, info):
        return parent.get("xmp:Rating") or 0


class Thumbnail(graphene.ObjectType):
    src = graphene.String(required=True, description="What to use for the `img[src]`")
    size = graphene.Int(required=True, description="maximum dimension of the image")


class ImageThumbs(graphene.ObjectType):
    small = graphene.Field(Thumbnail, description="An image suitable for a thumbnail")
    medium = graphene.Field(Thumbnail, description="An image suitable for mobile")
    large = graphene.Field(Thumbnail, description="An image suitable for a lightbox")

    def resolve_small(parent, info):
        request = info.context["request"]
        url = request.url_for("thumbs", path=str(parent["path"].relative_to(BASE_DIR)))
        return Thumbnail(src=f"{url}?size=200", size=200)

    def resolve_medium(parent, info):
        request = info.context["request"]
        url = request.url_for("thumbs", path=str(parent["path"].relative_to(BASE_DIR)))
        return Thumbnail(src=f"{url}?size=500", size=500)

    def resolve_large(parent, info):
        request = info.context["request"]
        url = request.url_for("thumbs", path=str(parent["path"].relative_to(BASE_DIR)))
        return Thumbnail(src=f"{url}?size=1000", size=1000)


class Image(graphene.ObjectType):
    path = graphene.ID()
    file_info = graphene.Field(ImageFileInfo)
    attributes = graphene.Field(ImageAttributes)
    iptc = graphene.Field(ImageIPTC)
    xmp = graphene.Field(ImageXMP, required=True)
    thumbs = graphene.Field(ImageThumbs, required=True)
    # WIP
    src = graphene.String(required=True)

    def resolve_path(parent, info):
        return parent["path"].relative_to(BASE_DIR)

    def resolve_file_info(parent, info):
        info = parent["path"].stat()
        return {
            "path": str(parent["path"]),
            "size": info.st_size,
            "created": info.st_ctime,
            "modified": info.st_mtime,
            "accessed": info.st_atime,
        }

    def resolve_attributes(parent, info):
        return PIL.Image.open(parent["path"])

    def resolve_iptc(parent, info):
        return IPTCInfo(parent["path"], inp_charset="utf_8")

    def resolve_xmp(parent, info):
        xmp = file_to_dict(str(parent["path"]))
        if XMP_NS_XMP not in xmp:
            return {}

        return {key: value for key, value, options in xmp[XMP_NS_XMP]}

    def resolve_src(parent, info):
        request = info.context["request"]
        return request.url_for("static", path=str(parent["path"].relative_to(BASE_DIR)))

    def resolve_thumbs(parent, info):
        return parent


class Album(graphene.ObjectType):
    path = graphene.ID()
    contents = relay.ConnectionField("gallery.schema.AlbumContentConnection")

    def resolve_contents(parent, info):
        paths = []
        for x in parent["path"].glob("*"):
            if x.is_dir() and x.name[0] not in ("_", "."):
                paths.append({"path": x, "type": "Album"})

            if x.is_file() and x.suffix and x.suffix in (".jpg",):
                paths.append({"path": x, "type": "Image"})
        return paths

    def resolve_path(parent, info):
        return parent["path"].relative_to(BASE_DIR)


class AlbumContent(graphene.Union):
    class Meta:
        types = (Image, Album)

    def resolve_type(parent, info):
        return parent["type"]


class AlbumContentConnection(relay.Connection):
    class Meta:
        node = AlbumContent

    class Edge:
        other = graphene.String(description="what does this do?")


class Query(graphene.ObjectType):
    image = graphene.Field(Image, path=graphene.NonNull(graphene.String))
    album = graphene.Field(Album, path=graphene.NonNull(graphene.String))

    def resolve_image(parent, info, *, path):
        # TODO prevent priveledge escalation ../../ paths
        # TODO use a loader to DRY with SetRatingPayload.mutate
        abs_path = Path(BASE_DIR, path)
        if not abs_path.exists():
            raise Exception("Image not found")
        # TODO this should probably be Image(path=abs_path)
        return {
            "path": abs_path,
        }

    def resolve_album(parent, info, *, path):
        # TODO prevent priveledge escalation ../../ paths
        abs_path = Path(BASE_DIR, path)
        if not abs_path.exists():
            raise Exception("Album not found")
        if not abs_path.is_dir():
            raise Exception("Album is not a directory")
        # TODO this should probably be Album(path=abs_path)
        return {
            "path": abs_path,
        }


# Mutations
###########


class SetRatingInput(graphene.InputObjectType):
    path = graphene.String(required=True, description="ID of the image")
    rating = graphene.Int(required=True, description="New rating, usually 1-5")


class SetRatingPayload(graphene.Mutation):
    image = graphene.Field(Image, required=True)

    class Arguments:
        input = SetRatingInput(required=True)

    def mutate(self, info, input):
        abs_path = Path(BASE_DIR, input["path"])
        if not abs_path.exists():
            raise Exception("Image not found")

        if not (isinstance(input["rating"], int) and -1 <= input["rating"] <= 5):
            raise Exception("Rating must be an integer from 1 to 5")

        image = {"path": abs_path}
        xmpfile = XMPFiles(file_path=str(abs_path), open_forupdate=True)
        xmp = xmpfile.get_xmp()
        # WISHLIST don't write if rating didn't change
        xmp.set_property(XMP_NS_XMP, "xmp:Rating", str(input["rating"]))
        if not xmpfile.can_put_xmp(xmp):
            raise Exception("Can't write xmp metadata back to image")

        xmpfile.put_xmp(xmp)
        xmpfile.close_file()
        return SetRatingPayload(image=image)


class Mutation(graphene.ObjectType):
    set_rating = SetRatingPayload.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
