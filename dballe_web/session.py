import dballe
from dballe import dbacsv
import datetime
import asyncio
import concurrent.futures
import shlex
import logging

log = logging.getLogger(__name__)


def _export_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt is not None else None


def _import_datetime(val):
    if not val:
        return None
    return datetime.datetime.strptime(val, "%Y-%m-%d %H:%M:%S")


class Filter:
    def __init__(self):
        self.ana_id = None
        self.rep_memo = None
        self.level = None
        self.trange = None
        self.var = None
        self.datemin = None
        self.datemax = None
        self.latmin = None
        self.latmax = None
        self.lonmin = None
        self.lonmax = None

    def to_tuple(self, o):
        return (self.ana_id, self.rep_memo, self.level, self.trange, self.var, self.datemin, self.datemax)

    def to_record(self):
        res = {}
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
        if self.latmin is not None:
            res["latmin"] = float(self.latmin)
        if self.latmax is not None:
            res["latmax"] = float(self.latmax)
        if self.lonmin is not None:
            res["lonmin"] = float(self.lonmin)
        if self.lonmax is not None:
            res["lonmax"] = float(self.lonmax)
        return res

    def to_dict(self):
        return {
            "ana_id": self.ana_id,
            "rep_memo": self.rep_memo,
            "level": None if self.level is None else [self.level, dballe.describe_level(*self.level)],
            "trange": None if self.trange is None else [self.trange, dballe.describe_trange(*self.trange)],
            "var": self.var,
            "datemin": _export_datetime(self.datemin),
            "datemax": _export_datetime(self.datemax),
            "latmin": self.latmin,
            "latmax": self.latmax,
            "lonmin": self.lonmin,
            "lonmax": self.lonmax,
        }

    @classmethod
    def from_dict(cls, data):
        res = cls()
        res.ana_id = data.get("ana_id")
        res.rep_memo = data.get("rep_memo")
        res.level = data.get("level")
        res.trange = data.get("trange")
        res.var = data.get("var")
        res.datemin = _import_datetime(data.get("datemin"))
        res.datemax = _import_datetime(data.get("datemax"))
        res.latmin = data.get("latmin")
        res.latmax = data.get("latmax")
        res.lonmin = data.get("lonmin")
        res.lonmax = data.get("lonmax")
        return res


class Revalidator:
    def __init__(self, session):
        self.session = session
        # Future for the current revalidation process
        self.current_future = None

    def _revalidate(self):
        try:
            with self.session.db.transaction() as tr:
                with self.session.explorer.rebuild() as updater:
                    updater.add_db(tr)
            self.current_future = None
            self.session.initialized = True
        except Exception:
            log.exception("Revalidate failed")
            return []

    @asyncio.coroutine
    def __call__(self):
        if self.current_future is None:
            self.current_future = self.session.loop.run_in_executor(self.session.executor, self._revalidate)
        yield from self.current_future


def station_to_dict(s):
    return (s.report, s.id, s.lat, s.lon, s.ident)


class Session:
    def __init__(self, db_url):
        self.loop = asyncio.get_event_loop()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.db_url = db_url
        self.db = dballe.DB.connect(self.db_url)
        self.filter = Filter()
        self.data_limit = 20
        self.explorer = dballe.DBExplorer()
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
                stations.append(station_to_dict(station))
            else:
                stations_disabled.append(station_to_dict(station))

        stats = self.explorer.stats

        return {
            "filter": self.filter.to_dict(),
            "filter_cmdline": " ".join(shlex.quote("{}={}".format(k, v)) for k, v in self.filter.to_record().items()),
            "stations": stations,
            "stations_disabled": stations_disabled,
            "rep_memo": self.explorer.reports,
            "level": [(tuple(x), dballe.describe_level(*x)) for x in self.explorer.levels],
            "trange": [(tuple(x), dballe.describe_trange(*x)) for x in self.explorer.tranges],
            "var": self.explorer.varcodes,
            "stats": {
                "datetime_min": _export_datetime(stats.datetime_min),
                "datetime_max": _export_datetime(stats.datetime_max),
                "count": stats.count,
            },
            "initialized": self.initialized,
            "data_limit": self.data_limit,
            "db_url": self.db_url,
        }

    @asyncio.coroutine
    def export(self, format, out):
        """
        Export the currently selected data to out.

        Note: for BUFR and CREX, export is run in an executor, so data being
        processed needs to make sure it handles being generated/handled on a
        different thread
        """
        if format in ("bufr", "crex"):
            def exporter():
                with self.db.transaction() as tr:
                    tr.export_to_file(self.filter.to_record(), format.upper(), out)
            yield from self.loop.run_in_executor(self.executor, exporter)
        elif format == "csv":
            def exporter():
                with self.db.transaction() as tr:
                    dbacsv.export(tr, self.filter.to_record(), out)
            yield from self.loop.run_in_executor(self.executor, exporter)

    @asyncio.coroutine
    def init(self):
        if not self.initialized:
            log.debug("Async setup")
            yield from self._revalidate()
        return self.explorer_to_dict()

    @asyncio.coroutine
    def set_filter(self, flt):
        log.debug("Session.set_filter")
        self.filter = Filter.from_dict(flt)
        yield from self.loop.run_in_executor(self.executor, self.explorer.set_filter, self.filter.to_record())
        return self.explorer_to_dict()

    @asyncio.coroutine
    def refresh_filter(self):
        log.debug("Session.refresh_filter")
        yield from self._revalidate()
        return self.explorer_to_dict()

    @asyncio.coroutine
    def get_data(self):
        log.debug("Session.get_data")

        def _get_data():
            query = self.filter.to_record()
            if self.data_limit is not None:
                query["limit"] = self.data_limit
            res = []
            with self.db.transaction() as tr:
                for rec in tr.query_data(query):
                    var = rec["variable"]
                    row = {
                        "i": rec["context_id"],
                        "r": rec["rep_memo"],
                        "s": rec["ana_id"],
                        "c": var.code,
                        "l": tuple(rec["level"]),
                        "t": tuple(rec["trange"]),
                        "d": _export_datetime(rec["datetime"]),
                        "v": var.get(),
                        "vt": var.info.type,
                    }
                    if var.info.type in ("integer", "decimal"):
                        row["vs"] = var.info.scale
                    res.append(row)
            return res
        records = yield from self.loop.run_in_executor(self.executor, _get_data)
        return records

    @asyncio.coroutine
    def get_station_data(self, id_station):
        def _get_data():
            query = {"ana_id": id_station}
            station = None
            res = []
            with self.db.transaction() as tr:
                for rec in tr.query_stations(query):
                    station = {
                        "id": rec["ana_id"],
                        "lat": float(rec["lat"]),
                        "lon": float(rec["lon"]),
                        "ident": rec["ident"],
                        "rep_memo": rec["rep_memo"],
                    }

                for rec in tr.query_station_data(query):
                    var = rec["variable"]
                    row = {
                        "i": rec["context_id"],
                        "c": var.code,
                        "v": var.get(),
                        "vt": var.info.type,
                    }
                    if var.info.type in ("integer", "decimal"):
                        row["vs"] = var.info.scale
                    res.append(row)
                return station, res
        station, records = yield from self.loop.run_in_executor(self.executor, _get_data)
        return station, records

    @asyncio.coroutine
    def get_station_data_attrs(self, id):
        def _get_data():
            with self.db.transaction() as tr:
                attrs = tr.attr_query_station(id)
            res = []
            for k, var in attrs.items():
                row = {
                    "c": k,
                    "v": var.get(),
                    "vt": var.info.type,
                }
                if var.info.type in ("integer", "decimal"):
                    row["vs"] = var.info.scale
                res.append(row)
            return res
        records = yield from self.loop.run_in_executor(self.executor, _get_data)
        return records

    @asyncio.coroutine
    def get_data_attrs(self, id):
        def _get_data():
            with self.db.transaction() as tr:
                attrs = tr.attr_query_data(id)
            res = []
            for k, var in attrs.items():
                row = {
                    "c": k,
                    "v": var.enq(),
                    "vt": var.info.type,
                }
                if var.info.type in ("integer", "decimal"):
                    row["vs"] = var.info.scale
                res.append(row)
            return res
        records = yield from self.loop.run_in_executor(self.executor, _get_data)
        return records

    @asyncio.coroutine
    def replace_station_data(self, rec):
        log.debug("Session.replace_station_data %r", rec)
        r = {"ana_id": int(rec["ana_id"])}
        if rec["vt"] == "decimal":
            r[rec["varcode"]] = float(rec["value"])
        elif rec["vt"] == "integer":
            r[rec["varcode"]] = int(rec["value"])
        else:
            r[rec["varcode"]] = rec["value"]
        self.db.insert_station_data(r, can_replace=True, can_add_stations=False)
        return (yield from self.get_station_data(rec["ana_id"]))

    @asyncio.coroutine
    def replace_data(self, rec):
        log.debug("Session.replace_data %r", rec)
        r = {}
        r["ana_id"] = int(rec["ana_id"])
        r["level"] = tuple(rec["level"])
        r["trange"] = tuple(rec["trange"])
        r["datetime"] = _import_datetime(rec["datetime"])
        if rec["vt"] == "decimal":
            r[rec["varcode"]] = float(rec["value"])
        elif rec["vt"] == "integer":
            r[rec["varcode"]] = int(rec["value"])
        else:
            r[rec["varcode"]] = rec["value"]
        self.db.insert_data(r, can_replace=True, can_add_stations=False)
        return (yield from self.get_data())

    @asyncio.coroutine
    def replace_station_data_attr(self, var_data, rec):
        log.debug("Session.replace_station_data_attr %r %r", var_data, rec)
        r = {}
        if rec["vt"] == "decimal":
            r[rec["c"]] = float(rec["v"])
        elif rec["vt"] == "integer":
            r[rec["c"]] = int(rec["v"])
        else:
            r[rec["c"]] = rec["v"]
        self.db.attr_insert_station(var_data["i"], r)
        return (yield from self.get_station_data_attrs(var_data["i"]))

    @asyncio.coroutine
    def replace_data_attr(self, var_data, rec):
        log.debug("Session.replace_data_attr %r %r", var_data, rec)
        r = {}
        if rec["vt"] == "decimal":
            r[rec["c"]] = float(rec["v"])
        elif var_data["vt"] == "integer":
            r[rec["c"]] = int(rec["v"])
        else:
            r[rec["c"]] = rec["v"]
        self.db.attr_insert_data(var_data["i"], r)
        return (yield from self.get_data_attrs(var_data["i"]))

    @asyncio.coroutine
    def set_data_limit(self, limit):
        log.debug("Session.set_data_limit %r", limit)
        self.data_limit = int(limit) if limit else None
        return (yield from self.get_data())
