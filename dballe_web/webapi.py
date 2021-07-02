from typing import Dict, Any
import threading
import datetime
import queue
import time
from flask import Blueprint, jsonify, make_response, request, current_app, Response
from flask.views import MethodView

api = Blueprint('api10', __name__, url_prefix='/api/1.0/')


class Exporter:
    """
    Turn a function writing to files to a generator as expected by Flask
    """
    def __init__(self, fmt: str):
        self.format = fmt
        self.db_session = current_app.db_session
        self.write_queue = queue.Queue(maxsize=64)
        self.thread = threading.Thread(target=self.write_loop)
        self.thread.start()

    def write_loop(self):
        """
        Executed in the subthread to export data to the write queue
        """
        try:
            self.db_session.export(format, self)
        finally:
            self.write_queue.put(None)

    def write(self, chunk: bytes):
        """
        Executed in subthread when it writes to its output file
        """
        self.write_queue.put(chunk)

    def generate(self):
        """
        Executed in the main thread to generate output in the response
        """
        while True:
            chunk = self.write_queue.get()
            if chunk is None:
                self.thread.join()
                break
            else:
                yield chunk


@api.route(r"/export/<format>")
def export(format):
    """
    Download data selected in the current section
    """
    fname = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    if format == "csv":
        mimetype = "text/csv"
    else:
        mimetype = "application/octet-stream"

    exporter = Exporter(format)

    res = Response(exporter.generate(), mimetype=mimetype, headers=[
        ("Content-Disposition", 'attachment; filename="{}.{}"'.format(fname, format)),
    ])
    # writer = WriteToHandler(self)
    # yield to_tornado_future(asyncio.ensure_future(self.application.session.export(format, writer)))
    return res


class APIView(MethodView):
    """
    Base code for all Web API views
    """
    def call_api(self, kwargs: Dict[str, Any]):
        try:
            result = self.api(**kwargs)
            current_app.logger.debug("API call %s %r result %r", self.__class__.__name__, kwargs, result)
            if not self.db_session.initialized:
                result["initializing"] = True
            result["time"] = time.time()
            return jsonify(result)
        except Exception as e:
            current_app.logger.error("API call error %s", e, exc_info=True)
            code = 500
            return make_response(jsonify({
                "error": True,
                "code": code,
                "message": str(e)
            }), code)

    @property
    def db_session(self):
        return current_app.db_session

    @classmethod
    def register(cls, name: str):
        api.add_url_rule(f"/{name}", view_func=cls.as_view(f"{name}"))


def register(name: str):
    def _register(cls):
        cls.register(name)
        return cls
    return _register


class APIViewGET(APIView):
    """
    Base code for all Web API GET views
    """
    def get(self, **kwargs):
        current_app.logger.debug("API GET call %s %r", self.__class__.__name__, kwargs)
        kwargs.update(request.args.items())
        return self.call_api(kwargs)


class APIViewPOST(APIView):
    """
    Base code for all Web API POST views
    """
    def post(self, **kwargs):
        current_app.logger.debug("API POST call %s %r", self.__class__.__name__, kwargs)
        kwargs.update(request.json.items())
        return self.call_api(kwargs)


@register("init")
class APIInit(APIViewGET):
    def api(self):
        return {
            "explorer": self.db_session.init(),
        }


@register("get_data")
class APIGetData(APIViewGET):
    def api(self):
        return {
            "rows": self.db_session.get_data(),
        }


@register("get_station_data")
class APIGetStationData(APIViewGET):
    def api(self, id_station):
        station, rows = self.db_session.get_station_data(int(id_station))
        return {
            "station": station,
            "rows": rows,
        }


@register("get_station_data_attrs")
class APIGetStationDataAttrs(APIViewGET):
    def api(self, id):
        return {
            "rows": self.db_session.get_station_data_attrs(int(id)),
        }


@register("get_data_attrs")
class APIGetDataAttrs(APIViewGET):
    def api(self, id):
        return {
            "rows": self.db_session.get_data_attrs(int(id)),
        }


@register("set_filter")
class APISetFilter(APIViewPOST):
    def api(self, filter):
        return {
            "explorer": self.db_session.set_filter(filter),
        }


@register("replace_station_data")
class ApiReplaceStationData(APIViewPOST):
    def api(self, rec):
        station, rows = self.db_session.replace_station_data(rec)
        return {
            "station": station,
            "rows": rows,
        }


@register("replace_data")
class ApiReplaceData(APIViewPOST):
    def api(self, rec):
        return {
            "rows": self.db_session.replace_data(rec),
        }


@register("replace_station_data_attr")
class APIReplaceStationDataAttr(APIViewPOST):
    def api(self, var_data, rec):
        return {
            "rows": self.db_session.replace_station_data_attr(var_data, rec),
        }


@register("replace_data_attr")
class APIReplaceDataAttr(APIViewPOST):
    def api(self, var_data, rec):
        return {
            "rows": self.db_session.replace_data_attr(var_data, rec),
        }


@register("set_data_limit")
class APISetDataLimit(APIViewPOST):
    def api(self, limit):
        return {
            "rows": self.db_session.set_data_limit(limit),
        }
