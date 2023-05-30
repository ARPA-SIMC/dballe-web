from unittest import mock, TestCase
import contextlib
import datetime
from flask import url_for
from dballe_web.unittest import DballeWebMixin


class WebAPIMixin(DballeWebMixin):
    @contextlib.contextmanager
    def client(self, time=100):
        with mock.patch("time.time", return_value=time):
            with self.app.test_client() as client:
                client.set_cookie("localhost", "Auth-Token", self.app.access_token)
                yield client

    def api_export(self, fmt: str, time: int = 100, **kwargs):
        with self.app.app_context():
            url = url_for("api10.export", format=fmt)

        with self.client(time=time) as client:
            return client.get(url, data=kwargs)

    def api_get(self, name: str, time: int = 100, **kwargs):
        with self.app.app_context():
            url = url_for(f"api10.{name}")

        with self.client(time=time) as client:
            return client.get(url, data=kwargs)

    def api_post(self, name: str, time: int = 100, **kwargs):
        with self.app.app_context():
            url = url_for(f"api10.{name}")

        with self.client(time=time) as client:
            return client.post(url, json=kwargs)


class TestEmpty(WebAPIMixin, TestCase):
    def test_get_data(self):
        self.app.db_session.init()
        res = self.api_get("get_data")
        self.assertEqual(res.get_json(), {"time": 100, "rows": []})

    def test_export(self):
        self.app.db_session.init()
        res = self.api_export("bufr")
        self.assertEqual(res.get_data(), b"")
        res = self.api_export("csv")
        self.assertEqual(res.get_data(), b"")


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
                'var': [
                    ['B01011', 'B01011: SHIP OR MOBILE LAND STATION IDENTIFIER'],
                    ['B01012', 'B01012: DIRECTION OF MOTION OF MOVING OBSERVING PLATFORM**'],
                ],
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

    def test_export(self):
        self.maxDiff = None
        self.app.db_session.init()

        res = self.api_export("bufr")
        self.assertEqual(res.headers["Content-Type"], "application/octet-stream")
        self.assertRegex(res.headers["Content-Disposition"], r'attachment; filename="\d{8}-\d{4}.bufr"')
        self.assertRegex(res.get_data(), br"^BUFR.+7777$")

        res = self.api_export("csv")
        self.assertEqual(res.headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertRegex(res.headers["Content-Disposition"], r'attachment; filename="\d{8}-\d{4}.csv"')
        self.assertEqual(res.get_data().decode().splitlines(), [
            '"1945-04-25 08:00:00; Level 10,11,15,22; Time range 20,111,222",,,,,',
            "Station,Latitude,Longitude,Network,Variable,Value",
            "1,12.34560,76.54320,synop,B01011,Hey Hey!!",
            "1,12.34560,76.54320,synop,B01012,500",
            "2,12.34560,76.54320,temp,B01011,Hey Hey!!",
            "2,12.34560,76.54320,temp,B01012,500",
        ])

    def test_set_filter(self):
        self.maxDiff = None
        self.app.db_session.init()

        res = self.api_post("set_filter", filter={"datemin": "1945-04-25 00:00:00", "datemax": "1945-04-25 12:00:00"})
        self.assertEqual(res.get_json(), {
            "time": 100,
            "explorer": {
                "data_limit": self.app.db_session.data_limit,
                "db_url": self.app.db_session.db_url,
                "filter": {
                    'ana_id': None,
                    'datemax': "1945-04-25 12:00:00",
                    'datemin': "1945-04-25 00:00:00",
                    'level': None,
                    'rep_memo': None,
                    'trange': None,
                    'var': None,
                    'latmin': None,
                    'latmax': None,
                    'lonmin': None,
                    'lonmax': None,
                },
                'filter_cmdline': "'datetimemin=1945-04-25 00:00:00' 'datetimemax=1945-04-25 12:00:00'",
                'initialized': True,
                'stations': [
                    ['synop', 1, 12.3456, 76.5432, None],
                    ['temp', 2, 12.3456, 76.5432, None]],
                'stations_disabled': [],
                'level': [[[10, 11, 15, 22], 'Layer from [10 11] to [15 22]']],
                'trange': [[[20, 111, 222], '20 111 222']],
                'rep_memo': ['synop', 'temp'],
                'var': [
                    ['B01011', 'B01011: SHIP OR MOBILE LAND STATION IDENTIFIER'],
                    ['B01012', 'B01012: DIRECTION OF MOTION OF MOVING OBSERVING PLATFORM**'],
                ],
                'stats': {
                    'count': 4,
                    'datetime_min': '1945-04-25 08:00:00',
                    'datetime_max': '1945-04-25 08:00:00',
                },
            },
        })
