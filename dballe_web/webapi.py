import time
import logging
import asyncio

log = logging.getLogger(__name__)


class WebAPIError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


class WebAPI:
    """
    Backend-independent functions exposed via REST or WebSocket APIs
    """
    def __init__(self, session):
        self.session = session
        self.loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def __call__(self, function=None, **kw):
        """
        Call a web API function by name and keyword arguments
        """
        log.debug("API call %s %r", function, kw)
        if function is None:
            log.debug("API call %s %s: function is missing", function, kw)
            return None
        f = getattr(self, "do_" + function)
        if f is None:
            log.debug("API call %s %s: function not found", function, kw)
            return None
        if asyncio.iscoroutinefunction(f):
            res = yield from f(**kw)
        else:
            res = f(**kw)
        log.debug("API call %s %r result %r", function, kw, res)
        if not self.session.initialized:
            res["initializing"] = True
        res["time"] = time.time()
        return res

    def do_ping(self, **kw):
        return {
            "pong": True,
        }

    @asyncio.coroutine
    def do_async_ping(self, **kw):
        return {
            "pong": True,
        }

    @asyncio.coroutine
    def do_get_data(self, **kw):
        return {
            "rows": (yield from self.session.get_data()),
        }

    @asyncio.coroutine
    def do_get_station_data(self, id_station, **kw):
        station, rows = (yield from self.session.get_station_data(int(id_station)))
        return {
            "station": station,
            "rows": rows,
        }

    @asyncio.coroutine
    def do_get_station_data_attrs(self, id, **kw):
        return {
            "rows": (yield from self.session.get_station_data_attrs(int(id))),
        }

    @asyncio.coroutine
    def do_get_data_attrs(self, id, **kw):
        return {
            "rows": (yield from self.session.get_data_attrs(int(id))),
        }

    @asyncio.coroutine
    def do_set_filter(self, filter, **kw):
        return {
            "explorer": (yield from self.session.set_filter(filter)),
        }

    @asyncio.coroutine
    def do_replace_station_data(self, rec, **kw):
        station, rows = (yield from self.session.replace_station_data(rec))
        return {
            "station": station,
            "rows": rows,
        }

    @asyncio.coroutine
    def do_replace_data(self, rec, **kw):
        return {
            "rows": (yield from self.session.replace_data(rec)),
        }

    @asyncio.coroutine
    def do_replace_station_data_attr(self, var_data, rec, **kw):
        return {
            "rows": (yield from self.session.replace_station_data_attr(var_data, rec)),
        }

    @asyncio.coroutine
    def do_replace_data_attr(self, var_data, rec, **kw):
        return {
            "rows": (yield from self.session.replace_data_attr(var_data, rec)),
        }

    @asyncio.coroutine
    def do_set_data_limit(self, limit, **kw):
        return {
            "rows": (yield from self.session.set_data_limit(limit)),
        }
