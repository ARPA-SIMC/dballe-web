from dballe_web.webapi import WebAPI
from dballe_web.session import Session
import datetime
from dballe_web.unittest import async_test, AsyncTestCase
from unittest import mock


class TestWebAPIMixin:
    def setUp(self):
        super().setUp()
        self.session = Session("sqlite::memory:")
        self.session.db.reset()
        self.api = WebAPI(self.session)


class TestPing(TestWebAPIMixin, AsyncTestCase):
    @async_test
    def test_ping(self):
        with mock.patch("time.time", return_value=100):
            res = yield from self.api("ping")
            self.assertEqual(res, {"time": 100, "initializing": True, "pong": True})

    @async_test
    def test_async_ping(self):
        with mock.patch("time.time", return_value=100):
            res = yield from self.api("ping")
            self.assertEqual(res, {"time": 100, "initializing": True, "pong": True})


class TestEmpty(TestWebAPIMixin, AsyncTestCase):
    @async_test
    def test_get_data(self):
        yield from self.session.refresh_filter()
        with mock.patch("time.time", return_value=100):
            res = yield from self.api("get_data")
            self.assertEqual(res, {"time": 100, "rows": []})


class TestInit(TestWebAPIMixin, AsyncTestCase):
    @async_test
    def test_not_initialized(self):
        with mock.patch("time.time", return_value=150):
            res = yield from self.api("init")
            self.assertEqual(res, {
                "time": 150,
                'explorer': {
                    "data_limit": self.session.data_limit,
                    "db_url": self.session.db_url,
                    'filter': {
                        'ana_id': None,
                        'datemax': None,
                        'datemin': None,
                        'level': None,
                        'rep_memo': None,
                        'trange': None,
                        'var': None,
                        'latmin': None,
                        'latmax': None,
                        'lonmin': None,
                        'lonmax': None,
                    },
                    'filter_cmdline': '',
                    'initialized': True,
                    'stations': [],
                    'stations_disabled': [],
                    'level': [],
                    'rep_memo': [],
                    'trange': [],
                    'var': [],
                    'stats': {
                        'datetime_min': None,
                        'datetime_max': None,
                        'count': 0
                    },
                },
            })


class TestBasic(TestWebAPIMixin, AsyncTestCase):
    def setUp(self):
        super().setUp()
        with self.session.db.transaction() as t:
            self.data = dict(
                    lat=12.34560, lon=76.54320,
                    datetime=datetime.datetime(1945, 4, 25, 8, 0, 0),
                    level=(10, 11, 15, 22),
                    trange=(20, 111, 222),
                    rep_memo="synop",
                    B01011="Hey Hey!!",
                    B01012=500)
            t.insert_data(self.data, False, True)

            self.data = dict(
                    lat=12.34560, lon=76.54320,
                    datetime=datetime.datetime(1945, 4, 25, 8, 0, 0),
                    level=(10, 11, 15, 22),
                    trange=(20, 111, 222),
                    rep_memo="temp",
                    B01011="Hey Hey!!",
                    B01012=500)
            t.insert_data(self.data, False, True)

    @async_test
    def test_init(self):
        with mock.patch("time.time", return_value=100):
            res = yield from self.api("init")
            self.maxDiff = None
            self.assertEqual(res, {
                "time": 100,
                "explorer": {
                    "data_limit": self.session.data_limit,
                    "db_url": self.session.db_url,
                    "filter": {
                        'ana_id': None,
                        'datemax': None,
                        'datemin': None,
                        'level': None,
                        'rep_memo': None,
                        'trange': None,
                        'var': None,
                        'latmin': None,
                        'latmax': None,
                        'lonmin': None,
                        'lonmax': None,
                    },
                    'filter_cmdline': '',
                    'initialized': True,
                    'stations': [
                        ('synop', 1, 12.3456, 76.5432, None),
                        ('temp', 2, 12.3456, 76.5432, None)],
                    'stations_disabled': [],
                    'level': [((10, 11, 15, 22), 'Layer from [10 11] to [15 22]')],
                    'trange': [((20, 111, 222), '20 111 222')],
                    'rep_memo': ['synop', 'temp'],
                    'var': ['B01011', 'B01012'],
                    'stats': {
                        'count': 4,
                        'datetime_min': '1945-04-25 08:00:00',
                        'datetime_max': '1945-04-25 08:00:00',
                    },
                },
            })

    @async_test
    def test_get_data(self):
        yield from self.session.refresh_filter()
        with mock.patch("time.time", return_value=100):
            res = yield from self.api("get_data")
            self.maxDiff = None
            self.assertEqual(res, {
                "time": 100,
                "rows": [{
                    "i": 1,
                    "r": "synop",
                    "s": 1,
                    "c": "B01011",
                    "l": (10, 11, 15, 22),
                    "t": (20, 111, 222),
                    "d": "1945-04-25 08:00:00",
                    "v": "Hey Hey!!",
                    "vt": "string",
                }, {
                    "i": 2,
                    "r": "synop",
                    "s": 1,
                    "c": "B01012",
                    "l": (10, 11, 15, 22),
                    "t": (20, 111, 222),
                    "d": "1945-04-25 08:00:00",
                    "v": 500,
                    "vt": "integer",
                    "vs": 0,
                }, {
                    "i": 3,
                    "r": "temp",
                    "s": 2,
                    "c": "B01011",
                    "l": (10, 11, 15, 22),
                    "t": (20, 111, 222),
                    "d": "1945-04-25 08:00:00",
                    "v": "Hey Hey!!",
                    "vt": "string",
                }, {
                    "i": 4,
                    "r": "temp",
                    "s": 2,
                    "c": "B01012",
                    "l": (10, 11, 15, 22),
                    "t": (20, 111, 222),
                    "d": "1945-04-25 08:00:00",
                    "v": 500,
                    "vt": "integer",
                    "vs": 0,
                }],
            })
