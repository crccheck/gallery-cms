import os

from starlette.applications import Starlette
from starlette.graphql import GraphQLApp
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from . import routes
from .schema import schema

BASE_DIR = os.getenv("BASE_DIR", os.path.dirname(os.path.abspath(__file__)))


class SpaStaticFiles(StaticFiles):
    """Staticfiles for single-page-apps"""

    async def lookup_path(self, path):
        full_path, stat_result = await super().lookup_path(path)
        if stat_result is None:
            return await super().lookup_path("./index.html")

        return full_path, stat_result


starlette_routes = [
    Route("/graphql", GraphQLApp(schema=schema)),
    Mount("/static", app=StaticFiles(directory=BASE_DIR), name="static"),
    Route("/thumbs/{path:path}", routes.thumbs, name="thumbs"),
    Mount("", app=SpaStaticFiles(directory="build", html=True)),
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
