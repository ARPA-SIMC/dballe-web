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

    async def __call__(self, function=None, **kw):
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
            res = await f(**kw)
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

    async def do_async_ping(self, **kw):
        return {
            "pong": True,
        }

    async def do_init(self, **kw):
        return {
            "explorer": await self.session.init(),
        }

    def do_get_filter_stats(self, **kw):
        return {
            "current": self.session.filter.to_dict(),
            "available": self.session.explorer_to_dict(),
        }

    def do_get_stations(self, **kw):
        return {
            "stations": self.session.explorer.all_stations,
        }

    async def do_get_data(self, **kw):
        return {
            "rows": await self.session.get_data(),
        }

    async def do_set_filter(self, filter, **kw):
        return {
            "explorer": await self.session.set_filter(filter),
        }
