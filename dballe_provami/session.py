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


class Session:
    def __init__(self, db_url):
        self.loop = asyncio.get_event_loop()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.db_url = db_url
        self.db = dballe.DB.connect_from_url(self.db_url)
        self.filter = Filter()
        self.explorer = dballe.Explorer()
        self.initialized = False

    def explorer_to_dict(self):
        if not self.initialized:
            return {"stations": [], "rep_memo": [], "level": [], "trange": [], "var": []}

        def level_key(l):
            return tuple((str(x) if x is not None else "") for x in l)

        def trange_key(t):
            return tuple((str(x) if x is not None else "") for x in t)

        return {
            "stations": self.explorer.stations,
            "rep_memo": self.explorer.reports,
            "level": [(tuple(x), dballe.describe_level(*x)) for x in self.explorer.levels],
            "trange": [(tuple(x), dballe.describe_trange(*x)) for x in self.explorer.tranges],
            "var": self.explorer.varcodes,
            # "datemin": self.datemin.strftime("%Y-%m-%d %H:%M:%S") if self.datemin is not None else None,
            # "datemax": self.datemax.strftime("%Y-%m-%d %H:%M:%S") if self.datemin is not None else None,
        }

    async def set_filter(self, flt):
        log.debug("Session.set_filter")
        self.filter = Filter.from_dict(flt)
        await self.loop.run_in_executor(self.executor, self.explorer.set_filter, self.filter.to_record())

    async def refresh_filter(self):
        log.debug("Session.refresh_filter")

        def _revalidate():
            try:
                with self.db.transaction() as tr:
                    self.explorer.revalidate(tr)
            except Exception:
                log.exception("Revalidate failed")
                return []

        await self.loop.run_in_executor(self.executor, _revalidate)
        self.initialized = True
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
