import os
import json
import tornado.ioloop
import tornado.web
from tornado.web import url
from .webapi import WebAPI, WebAPIError
from .session import Session
import asyncio
import logging

log = logging.getLogger(__name__)


class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class RestGET(tornado.web.RequestHandler):
    """
    WebAPI front-end for GET requests
    """
    def initialize(self, function, **kwargs):
        self.function = function
        self.kwargs = kwargs

    async def get(self, **kwargs):
        self.kwargs.update(kwargs)
        try:
            self.write(await self.application.webapi(self.function, **self.kwargs))
        except WebAPIError as e:
            self.set_status(e.code, str(e))
            self.write({
                "error": True,
                "code": e.code,
                "message": str(e)
            })


class RestPOST(tornado.web.RequestHandler):
    """
    WebAPI front-end for POST requests
    """
    def initialize(self, function, **kwargs):
        self.function = function
        self.kwargs = kwargs

    async def post(self, **kwargs):
        args = json.loads(self.request.body.decode("utf8"))
        args.update(kwargs)
        args.update(self.kwargs)
        try:
            self.write(await self.application.webapi(self.function, **args))
        except WebAPIError as e:
            self.set_status(e.code, str(e))
            self.write({
                "error": True,
                "code": e.code,
                "message": str(e)
            })


class Application(tornado.web.Application):
    def __init__(self, db_url, **settings):
        self.loop = asyncio.get_event_loop()
        self.session = Session(db_url)

        urls = [
            url(r"/", HomeHandler, name="home"),
            url(r"/api/1.0/ping", RestGET, kwargs={"function": "ping"}, name="api1.0_ping"),
            url(r"/api/1.0/async_ping", RestGET, kwargs={"function": "async_ping"}, name="api1.0_async_ping"),
            url(r"/api/1.0/init", RestGET, kwargs={"function": "init"}, name="api1.0_init"),
            url(r"/api/1.0/get_filter_stats", RestGET, kwargs={"function": "get_filter_stats"}, name="api1.0_get_filter_stats"),
            url(r"/api/1.0/get_data", RestGET, kwargs={"function": "get_data"}, name="api1.0_get_data"),
            url(r"/api/1.0/get_stations", RestGET, kwargs={"function": "get_stations"}, name="api1.0_get_stations"),
            url(r"/api/1.0/set_filter", RestPOST, kwargs={"function": "set_filter"}, name="api1.0_set_filter"),
        ]

        self.webapi = WebAPI(self.session)

        settings.setdefault("static_path", os.path.join(os.path.dirname(__file__), "static"))
        settings.setdefault("template_path", os.path.join(os.path.dirname(__file__), "templates"))
        # FIXME: disable in production
        settings.setdefault("compiled_template_cache", False)
        settings.setdefault("debug", True)
        # settings.setdefault("cookie_secret", "random string")
        # settings.setdefault("xsrf_cookies", True)

        super().__init__(urls, **settings)
