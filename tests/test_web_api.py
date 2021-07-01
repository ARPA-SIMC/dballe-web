from unittest import mock, TestCase
import contextlib
import datetime
from flask import url_for
from dballe_web.unittest import DballeWebMixin


class WebAPIMixin(DballeWebMixin):
    @contextlib.contextmanager
    def test_client(self, time=100):
        with mock.patch("time.time", return_value=time):
            with self.app.test_client() as client:
                yield client

    def api_get(self, name: str, time: int = 100, **kwargs):
        with self.app.app_context():
            url = url_for(f"api10.{name}")

        with self.test_client(time=time) as client:
            return client.get(url, data=kwargs)

    def api_post(self, name: str, time: int = 100, **kwargs):
        with self.app.app_context():
            url = url_for(f"api10.{name}")

        with self.test_client(time=time) as client:
            return client.get(url, json=kwargs)


# class TestPing(TestWebAPIMixin, TestCase):
#     @async_test
#     def test_ping(self):
#         with mock.patch("time.time", return_value=100):
#             res = yield from self.api("ping")
#             self.assertEqual(res, {"time": 100, "initializing": True, "pong": True})
#
#     @async_test
#     def test_async_ping(self):
#         with mock.patch("time.time", return_value=100):
#             res = yield from self.api("ping")
#             self.assertEqual(res, {"time": 100, "initializing": True, "pong": True})


class TestEmpty(WebAPIMixin, TestCase):
    def test_get_data(self):
        self.app.db_session.init()
        res = self.api_get("get_data")
        self.assertEqual(res.get_json(), {"time": 100, "rows": []})


class TestInit(WebAPIMixin, TestCase):
    def test_not_initialized(self):
        res = self.api_get("init")
        self.assertEqual(res.get_json(), {
                "time": 100,
                'explorer': {
                    "data_limit": self.app.db_session.data_limit,
                    "db_url": self.app.db_session.db_url,
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
            }
        )


class TestBasic(WebAPIMixin, TestCase):
    def setUp(self):
        super().setUp()
        with self.app.db.transaction() as t:
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

    def test_init(self):
        res = self.api_get("init")
        self.maxDiff = None
        self.assertEqual(res.get_json(), {
            "time": 100,
            "explorer": {
                "data_limit": self.app.db_session.data_limit,
                "db_url": self.app.db_session.db_url,
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
                    ['synop', 1, 12.3456, 76.5432, None],
                    ['temp', 2, 12.3456, 76.5432, None]],
                'stations_disabled': [],
                'level': [[[10, 11, 15, 22], 'Layer from [10 11] to [15 22]']],
                'trange': [[[20, 111, 222], '20 111 222']],
                'rep_memo': ['synop', 'temp'],
                'var': ['B01011', 'B01012'],
                'stats': {
                    'count': 4,
                    'datetime_min': '1945-04-25 08:00:00',
                    'datetime_max': '1945-04-25 08:00:00',
                },
            },
        })

    def test_get_data(self):
        self.app.db_session.init()
        res = self.api_get("get_data")
        self.maxDiff = None
        self.assertEqual(res.get_json(), {
            "time": 100,
            "rows": [{
                "i": 1,
                "r": "synop",
                "s": 1,
                "c": "B01011",
                "l": [10, 11, 15, 22],
                "t": [20, 111, 222],
                "d": "1945-04-25 08:00:00",
                "v": "Hey Hey!!",
                "vt": "string",
            }, {
                "i": 2,
                "r": "synop",
                "s": 1,
                "c": "B01012",
                "l": [10, 11, 15, 22],
                "t": [20, 111, 222],
                "d": "1945-04-25 08:00:00",
                "v": 500,
                "vt": "integer",
                "vs": 0,
            }, {
                "i": 3,
                "r": "temp",
                "s": 2,
                "c": "B01011",
                "l": [10, 11, 15, 22],
                "t": [20, 111, 222],
                "d": "1945-04-25 08:00:00",
                "v": "Hey Hey!!",
                "vt": "string",
            }, {
                "i": 4,
                "r": "temp",
                "s": 2,
                "c": "B01012",
                "l": [10, 11, 15, 22],
                "t": [20, 111, 222],
                "d": "1945-04-25 08:00:00",
                "v": 500,
                "vt": "integer",
                "vs": 0,
            }],
        })
