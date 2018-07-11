import dballe
import asyncio
import concurrent.futures
import logging

log = logging.getLogger(__name__)


def _tuple_to_string(t):
    if t is None:
        return None
    return ",".join(str(x) if x is not None else "" for x in t)


def _tuple_from_string(t):
    if t is None:
        return None
    return tuple(int(x) if x else None for x in t.split(","))


class Filter:
    def __init__(self):
        self.ana_id = None
        self.rep_memo = None
        self.level = None
        self.trange = None
        self.var = None
        self.datemin = None
        self.datemax = None

    def to_tuple(self, o):
        return (self.ana_id, self.rep_memo, self.level, self.trange, self.var, self.datemin, self.datemax)

    def to_record(self):
        res = dballe.Record()
        if self.ana_id is not None:
            res["ana_id"] = self.ana_id
        if self.rep_memo is not None:
            res["rep_memo"] = self.rep_memo
        if self.level is not None:
            res["level"] = tuple(self.level)
        if self.trange is not None:
            res["trange"] = tuple(self.trange)
        if self.var is not None:
            res["var"] = self.var
        if self.datemin is not None:
            res["datemin"] = self.datemin
        if self.datemax is not None:
            res["datemax"] = self.datemax
        return res

    def to_dict(self):
        return {
            "ana_id": self.ana_id,
            "rep_memo": self.rep_memo,
            "level": None if self.level is None else [_tuple_to_string(self.level), dballe.describe_level(*self.level)],
            "trange": None if self.trange is None else [_tuple_to_string(self.trange), dballe.describe_trange(*self.trange)],
            "var": self.var,
            "datemin": self.datemin.strftime("%Y-%m-%d %H:%M:%S") if self.datemin is not None else None,
            "datemax": self.datemax.strftime("%Y-%m-%d %H:%M:%S") if self.datemin is not None else None,
        }

    @classmethod
    def from_dict(cls, data):
        res = cls()
        res.ana_id = data.get("ana_id")
        res.rep_memo = data.get("rep_memo")
        res.level = _tuple_from_string(data.get("level"))
        res.trange = _tuple_from_string(data.get("trange"))
        res.var = data.get("var")
        res.datemin = data.get("datemin")
        res.datemax = data.get("datemax")
        return res


class Revalidator:
    def __init__(self, session):
        self.session = session
        # Future for the current revalidation process
        self.current_future = None

    def _revalidate(self):
        try:
            with self.session.db.transaction() as tr:
                self.session.explorer.revalidate(tr)
            self.current_future = None
            self.session.initialized = True
        except Exception:
            log.exception("Revalidate failed")
            return []

    async def __call__(self):
        if self.current_future is None:
            self.current_future = self.session.loop.run_in_executor(self.session.executor, self._revalidate)
        await self.current_future


class Session:
    def __init__(self, db_url):
        self.loop = asyncio.get_event_loop()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.db_url = db_url
        self.db = dballe.DB.connect_from_url(self.db_url)
        self.filter = Filter()
        self.explorer = dballe.Explorer()
        self.initialized = False
        self._revalidate = Revalidator(self)

    def explorer_to_dict(self):
        if not self.initialized:
            return {"stations": [], "rep_memo": [], "level": [], "trange": [], "var": []}

        def level_key(l):
            return tuple((str(x) if x is not None else "") for x in l)

        def trange_key(t):
            return tuple((str(x) if x is not None else "") for x in t)

        # Dispatch stations between currently selectable and all other stations
        current_stations_set = frozenset(self.explorer.stations)
        stations = []
        stations_disabled = []
        for station in self.explorer.all_stations:
            if station in current_stations_set:
                stations.append(station)
            else:
                stations_disabled.append(station)

        return {
            "filter": self.filter.to_dict(),
            "stations": stations,
            "stations_disabled": stations_disabled,
            "rep_memo": self.explorer.reports,
            "level": [(tuple(x), dballe.describe_level(*x)) for x in self.explorer.levels],
            "trange": [(tuple(x), dballe.describe_trange(*x)) for x in self.explorer.tranges],
            "var": self.explorer.varcodes,
            # "datemin": self.datemin.strftime("%Y-%m-%d %H:%M:%S") if self.datemin is not None else None,
            # "datemax": self.datemax.strftime("%Y-%m-%d %H:%M:%S") if self.datemin is not None else None,
            "initialized": self.initialized,
        }

    async def export(self, format, out):
        """
        Export the currently selected data to out.

        Note: for BUFR and CREX, export is run in an executor, so data being
        processed needs to make sure it handles being generated/handled on a
        different thread
        """
        if format in ("BUFR", "CREX"):
            def exporter():
                with self.db.transaction() as tr:
                    tr.export_to_file(self.filter.to_record(), format, out)
            await self.loop.run_in_executor(self.executor, exporter)

    async def init(self):
        if not self.initialized:
            log.debug("Async setup")
            await self._revalidate()
        return self.explorer_to_dict()

    async def set_filter(self, flt):
        log.debug("Session.set_filter")
        self.filter = Filter.from_dict(flt)
        await self.loop.run_in_executor(self.executor, self.explorer.set_filter, self.filter.to_record())
        return self.explorer_to_dict()

    async def refresh_filter(self):
        log.debug("Session.refresh_filter")
        await self._revalidate()
        return self.explorer_to_dict()

    async def get_data(self, limit=20):
        log.debug("Session.get_data")

        def _get_data():
            query = self.filter.to_record()
            if limit is not None:
                query["limit"] = limit
            res = []
            for rec in self.db.query_data(query):
                res.append([
                    rec["rep_memo"],
                    rec["ana_id"],
                    rec["var"],
                    tuple(rec["level"]),
                    tuple(rec["trange"]),
                    rec["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                    rec[rec["var"]],
                ])
            return res
        records = await self.loop.run_in_executor(self.executor, _get_data)
        return records
