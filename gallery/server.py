import os
from pathlib import Path
from textwrap import dedent

import graphene
from graphene import relay
from iptcinfo3 import IPTCInfo
from libxmp.consts import XMP_NS_XMP
from libxmp.utils import file_to_dict
from starlette.applications import Starlette
from starlette.graphql import GraphQLApp
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from . import routes


BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.abspath(__file__)))


class ImageFileInfo(graphene.ObjectType):
    """
    meta information about the `Image`
    """

    path = graphene.String()
    size = graphene.Int()
    created = graphene.Int()
    modified = graphene.Int()
    accessed = graphene.Int()


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


class Image(graphene.ObjectType):
    path = graphene.ID()
    file_info = graphene.Field(ImageFileInfo)
    iptc = graphene.Field(ImageIPTC)
    xmp = graphene.Field(ImageXMP)
    # WIP
    src = graphene.String()
    thumb = graphene.String()

    def resolve_file_info(parent, info):
        info = parent["path"].stat()
        return {
            "path": str(parent["path"]),
            "size": info.st_size,
            "created": info.st_ctime,
            "modified": info.st_mtime,
            "accessed": info.st_atime,
        }

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

    def resolve_thumb(parent, info):
        request = info.context["request"]
        return request.url_for("thumbs", path=str(parent["path"].relative_to(BASE_DIR)))


class Album(graphene.ObjectType):
    path = graphene.ID()
    contents = relay.ConnectionField("gallery.server.AlbumContentConnection")

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
        abs_path = Path(BASE_DIR, path)
        if not abs_path.exists():
            raise Exception("Image not found")
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
        return {
            "path": abs_path,
        }


starlette_routes = [
    Route("/graphql", GraphQLApp(schema=graphene.Schema(query=Query))),
    Mount("/static", app=StaticFiles(directory=BASE_DIR), name="static"),
    Route("/thumbs/{path:path}", routes.thumbs, name="thumbs"),
]

middleware = [
    Middleware(
        # https://www.starlette.io/middleware/#corsmiddleware
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        # allow_headers=["*"]
    )
]

app = Starlette(routes=starlette_routes, middleware=middleware)
