from sockjs.tornado import SockJSRouter, SockJSConnection
import asyncio
import json
import logging


class Connection(SockJSConnection):
    """
    Route all relevant socket.io methods to their implementation in the hub
    """
    log = logging.getLogger("wsconnection.connection")
    hub = None

    def on_open(self, info):
        # self.log.info("on_open %s %s", self, info.ip)
        self.hub._on_open(self, info)

    def on_close(self):
        # self.log.info("on_close %s", self)
        self.hub._on_close(self)

    def on_message(self, message: str):
        # self.log.info("on_message %s %s", self, message)
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            self.log.warn("%s: client sent malformed JSON: %r", self, message)
        else:
            self.hub._on_client_message(self, payload)


class Hub:
    """
    Central management of websocket connections.

    This takes care of setting up the main router, and storing dispatchers for
    virtual channels.
    """
    log = logging.getLogger("wsconnection.hub")

    def __init__(self, application):
        self.loop = asyncio.get_event_loop()
        self.application = application
        self.router = SockJSRouter(Connection, "/sockjs")

        # Hackish way to make Connection able to talk to us
        Connection.hub = self

        # Map connection -> sockjs.tornado.session.ConnectionInfo
        # see http://sockjs-tornado.readthedocs.org/en/latest/mod_session.html#sockjs.tornado.session.ConnectionInfo
        self.connection_info = {}

        # List of (dict, callable) with subscriptions for incoming messages from clients.
        # If the dict matches the incoming message, callable will be called
        # passing the Connection and the message.
        self.server_subscriptions = []

    def broadcast(self, message: dict):
        self.log.debug("Broadcast message %r", message)
        encoded = json.dumps(message)
        clients = list(self.connection_info)
        if clients:
            clients[0].broadcast(clients, encoded)

    def _on_open(self, conn: Connection, info):
        self.log.info("Connection open from %s for %s", info.ip, info.path)
        # Store the connection information to pass it to the channel
        # constructor when a message is received
        self.connection_info[conn] = info

    def _on_close(self, conn: Connection):
        # Remove all information for this connection
        del self.connection_info[conn]

    def _on_client_message(self, conn: Connection, payload: dict):
        self.log.debug("On client message %r: %r", conn, payload)
        for filter, callback in self.server_subscriptions:
            if filter.items() < payload.items():
                f = callback(conn, payload)
                if asyncio.iscoroutine(f):
                    self.loop.create_task(f)
                elif isinstance(f, asyncio.Future):
                    self.loop.create_task(f)

    def subscribe(self, filter, callback):
        self.server_subscriptions.append((filter, callback))
