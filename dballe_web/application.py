from typing import TYPE_CHECKING
import random
import string
from flask import Flask, render_template, redirect, abort, current_app, request
from .session import Session


if TYPE_CHECKING:
    import dballe


class Application(Flask):
    access_token_chars: str = string.ascii_letters + string.digits

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.db: dballe.DB = None
        self.db_session: Session = None
        rnd = random.SystemRandom()
        self.access_token = ''.join(rnd.choices(self.access_token_chars, k=16))

    def set_dballe_url(self, db_url: str):
        self.db_session = Session(db_url)
        self.db = self.db_session.db


# See https://flask.palletsprojects.com/en/2.0.x/patterns/appfactories/
def create_app(db_url: str):
    app = Application(__name__)
    app.set_dballe_url(db_url)

    from .webapi import api
    app.register_blueprint(api)

    @app.before_request
    def check_access_token():
        # TODO: all methods should be ratelimited
        if request.endpoint == "start":
            # The start method should not be protected, as it's the entry point
            return
        auth_token = request.cookies.get("Auth-Token")
        if current_app.access_token is not None and auth_token != current_app.access_token:
            abort(403)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/start/<token>")
    def start(token: str):
        if token != current_app.access_token:
            abort(403)

        response = redirect("/")
        response.set_cookie("Auth-Token", token)
        return response

    return app
