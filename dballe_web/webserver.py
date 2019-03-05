import os
import json
import tornado.ioloop
import tornado.web
from tornado.web import url
from tornado.platform.asyncio import to_tornado_future
from tornado import gen
from .webapi import WebAPI, WebAPIError
from .session import Session
import datetime
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

    @gen.coroutine
    def get(self, **kwargs):
        self.kwargs.update(kwargs)
        for name, vals in self.request.query_arguments.items():
            self.kwargs[name] = vals[-1]
        try:
            self.write((yield to_tornado_future(self.application.webapi(self.function, **self.kwargs))))
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

    @gen.coroutine
    def post(self, **kwargs):
        args = json.loads(self.request.body.decode("utf8"))
        args.update(kwargs)
        args.update(self.kwargs)
        try:
            self.write((yield to_tornado_future(self.application.webapi(self.function, **args))))
        except WebAPIError as e:
            self.set_status(e.code, str(e))
            self.write({
                "error": True,
                "code": e.code,
                "message": str(e)
            })


class WriteToHandler:
    def __init__(self, handler, cluster_size=1):
        self.loop = asyncio.get_event_loop()
        self.handler = handler
        self.cluster = []
        self.cluster_size = cluster_size

    def write(self, chunk):
        self.cluster.append(chunk)
        if len(self.cluster) > self.cluster_size:
            self.flush()

    def flush(self):
        cluster = self.cluster
        self.cluster = []

        def do_flush():
            for c in cluster:
                self.handler.write(c)
            self.handler.flush()

        self.loop.call_soon_threadsafe(do_flush)


class Export(tornado.web.RequestHandler):
    """
    Download data selected in the current section
    """
    @asyncio.coroutine
    def get(self, format, **kwargs):
        fname = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        self.set_header("Content-Disposition", 'attachment; filename="{}.{}"'.format(fname, format))
        if format == "csv":
            self.set_header("Content-Type", "text/csv")
        else:
            self.set_header("Content-Type", "application/octet-stream")
        writer = WriteToHandler(self)
        yield from self.application.session.export(format, writer)


class Application(tornado.web.Application):
    def __init__(self, db_url, **settings):
        self.loop = asyncio.get_event_loop()
        self.session = Session(db_url)

        urls = [
            url(r"/", HomeHandler, name="home"),
            url(r"/api/1.0/ping", RestGET, kwargs={"function": "ping"}, name="api1.0_ping"),
            url(r"/api/1.0/async_ping", RestGET, kwargs={"function": "async_ping"}, name="api1.0_async_ping"),
            url(r"/api/1.0/init", RestGET, kwargs={"function": "init"}, name="api1.0_init"),
            url(r"/api/1.0/get_data", RestGET, kwargs={"function": "get_data"}, name="api1.0_get_data"),
            url(r"/api/1.0/get_station_data", RestGET,
                kwargs={"function": "get_station_data"}, name="api1.0_get_station_data"),
            url(r"/api/1.0/get_station_data_attrs", RestGET,
                kwargs={"function": "get_station_data_attrs"}, name="api1.0_get_station_data_attrs"),
            url(r"/api/1.0/get_data_attrs", RestGET,
                kwargs={"function": "get_data_attrs"}, name="api1.0_get_data_attrs"),
            url(r"/api/1.0/set_filter", RestPOST,
                kwargs={"function": "set_filter"}, name="api1.0_set_filter"),
            url(r"/api/1.0/replace_station_data", RestPOST, kwargs={"function": "replace_station_data"},
                name="api1.0_replace_station_data"),
            url(r"/api/1.0/replace_data", RestPOST,
                kwargs={"function": "replace_data"}, name="api1.0_replace_data"),
            url(r"/api/1.0/replace_station_data_attr", RestPOST,
                kwargs={"function": "replace_station_data_attr"}, name="api1.0_replace_station_data_attr"),
            url(r"/api/1.0/replace_data_attr", RestPOST,
                kwargs={"function": "replace_data_attr"}, name="api1.0_replace_data_attr"),
            url(r"/api/1.0/set_data_limit", RestPOST,
                kwargs={"function": "set_data_limit"}, name="api1.0_set_data_limit"),
            url(r"/api/1.0/export/(?P<format>\w+)", Export, name="export"),
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

    @asyncio.coroutine
    def async_setup(self):
        yield from self.session.init()
