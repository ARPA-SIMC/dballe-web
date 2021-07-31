import logging
import getpass
import socket
import sys
from dballe_web.application import create_app, Server

try:
    import coloredlogs
except ModuleNotFoundError:
    coloredlogs = None


class DballeWeb:
    def __init__(self, args):
        self.args = args
        self.start_url = None
        self.port = None
        self.forwarded_start_url = None

        if args.debug:
            self.log_level = logging.DEBUG
        elif args.verbose:
            self.log_level = logging.INFO
        else:
            self.log_level = logging.WARN

    def start_flask(self):
        app = create_app(self.args.db)

        server = Server(
                host='127.0.0.1',
                port=0 if self.args.port is None else int(self.args.port),
                app=app)

        self.port = server.socket.getsockname()[1]
        if self.args.devel:
            app.access_token = None
            self.start_url = f"http://localhost:{self.port}"
            self.forwarded_start_url = f"http://localhost:5000/"
        else:
            self.start_url = f"http://localhost:{self.port}/start/{app.access_token}"
            self.forwarded_start_url = f"http://localhost:5000/start/{app.access_token}"

        return server


class CLI(DballeWeb):
    def start(self):
        FORMAT = "%(asctime)-15s %(levelname)s %(name)s %(message)s"

        if coloredlogs is not None:
            coloredlogs.install(level=self.log_level, fmt=FORMAT, stream=sys.stderr)
        else:
            logging.basicConfig(level=self.log_level, stream=sys.stderr, format=FORMAT)

        self.server = self.start_flask()

        print(f" * Running on {self.start_url} (Press CTRL+C to quit)")
        print(f" * Port forwarding command: ssh {getpass.getuser()}@{socket.getfqdn()} -NL 5000:localhost:{self.port}")
        print(f" * Port forwarding URL: {self.forwarded_start_url}")

        self.server.serve_forever()
