from typing import TYPE_CHECKING
from flask import Flask, render_template
from .session import Session


if TYPE_CHECKING:
    import dballe


class Application(Flask):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.db: dballe.DB = None
        self.db_session: Session = None

    def set_dballe_url(self, db_url: str):
        self.db_session = Session(db_url)
        self.db = self.db_session.db


# See https://flask.palletsprojects.com/en/2.0.x/patterns/appfactories/
def create_app(db_url: str):
    app = Application(__name__)
    app.set_dballe_url(db_url)

    from .webapi import api
    app.register_blueprint(api)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


# Old code with automatic port allocation
#
# class DballeWeb:
#     def __init__(self):
#         self.db_url = options.db
#         self.web_host = "localhost"
#         self.web_port = options.web_port
#
#     def setup(self):
#         # Set up web server on a free port
#         self.application = Application(self.db_url)
#
#         if self.web_port is None:
#             sockets = tornado.netutil.bind_sockets(0, '127.0.0.1')
#             self.web_port = sockets[0].getsockname()[:2][1]
#             server = tornado.httpserver.HTTPServer(self.application)
#             server.add_sockets(sockets)
#         else:
#             server = tornado.httpserver.HTTPServer(self.application)
#             server.listen(self.web_port)
