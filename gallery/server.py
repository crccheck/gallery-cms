import os
from pathlib import Path

import graphene
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.graphql import GraphQLApp
from iptcinfo3 import IPTCInfo


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
        return parent["caption/abstract"].decode("utf-8")

    def resolve_keywords(parent, info):
        return [x.decode("utf-8") for x in parent["keywords"]]


class Image(graphene.ObjectType):
    path = graphene.ID()
    file_info = graphene.Field(ImageFileInfo)
    iptc = graphene.Field(ImageIPTC)

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
        return IPTCInfo(parent["path"])


class Album(graphene.ObjectType):
    path = graphene.ID()
    contents = graphene.List("gallery.server.AlbumContents")

    def resolve_contents(parent, info):
        paths = []
        for x in parent["path"].glob("*"):
            if x.is_dir() and not x.name.startswith("_"):
                paths.append({"path": x, "type": "Album"})

            if x.is_file() and x.suffix in (".jpg"):
                paths.append({"path": x, "type": "Image"})
        return paths


class AlbumContents(graphene.Union):
    class Meta:
        types = (Image, Album)

    def resolve_type(parent, info):
        return parent["type"]


class Query(graphene.ObjectType):
    image = graphene.Field(Image, path=graphene.NonNull(graphene.String))
    album = graphene.Field(Album, path=graphene.NonNull(graphene.String))

    def resolve_image(parent, info, *, path):
        # TODO prevent priveledge escalation ../../ paths
        abs_path = Path(".", path)
        if not abs_path.exists():
            raise Exception("Image not found")
        return {
            "path": abs_path,
        }

    def resolve_album(parent, info, *, path):
        # TODO prevent priveledge escalation ../../ paths
        abs_path = Path(".", path)
        if not abs_path.exists():
            raise Exception("Album not found")
        if not abs_path.is_dir():
            raise Exception("Album is not a directory")
        return {
            "path": abs_path,
        }


routes = [Route("/graphql", GraphQLApp(schema=graphene.Schema(query=Query)))]

app = Starlette(routes=routes)
