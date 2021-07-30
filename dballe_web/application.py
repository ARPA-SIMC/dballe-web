from typing import TYPE_CHECKING, Tuple, Callable, IO
import selectors
import secrets
from flask import Flask, render_template, redirect, abort, current_app, request
import werkzeug.serving
from .session import Session


if TYPE_CHECKING:
    import dballe


class Application(Flask):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.db: dballe.DB = None
        self.db_session: Session = None
        self.access_token = secrets.token_urlsafe()

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


class StopServer(Exception):
    pass


class Server(werkzeug.serving.ThreadedWSGIServer):
    """
    Customized http server that allows handling other kind of events in its
    event loop
    """
    if hasattr(selectors, 'PollSelector'):
        _ServerSelector = selectors.PollSelector
    else:
        _ServerSelector = selectors.SelectSelector

    def serve_forever(self, events: Tuple[Tuple[IO, int, Callable[[int], None]]] = ()):
        """
        Events can be a tuple of (fileobj, events, function) and can list
        further functions to be called when events happen in the server event
        loop
        """
        try:
            with self._ServerSelector() as selector:
                server_key = selector.register(self, selectors.EVENT_READ)

                # Register custom events
                other_events = {}
                for fileobj, events, func in events:
                    key = selector.register(fileobj, events)
                    other_events[key] = func

                while True:
                    for key, events in selector.select():
                        if key == server_key:
                            self._handle_request_noblock()
                        else:
                            # Process custom events
                            try:
                                func = other_events.get(key)
                                if func is not None:
                                    func(events)
                            except StopServer:
                                return

                    self.service_actions()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()
