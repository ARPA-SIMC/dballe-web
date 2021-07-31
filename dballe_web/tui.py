from typing import Tuple, ContextManager
import collections
import contextlib
import webbrowser
import selectors
import datetime
import logging
import getpass
import socket
import curses
import sys
import os
from .ui import DballeWeb
from .application import StopServer

log = logging.getLogger(__name__)


class LogWindow:
    def __init__(self, window):
        self.window = window
        self.window.scrollok(True)
        self.window.idlok(True)
        self.window.leaveok(True)
        self.posy = 0

        # Screen attributes for the given log messages
        # Default RGB values for these colors are set in the Palette configuration of the terminal
        normal = curses.A_NORMAL
        if curses.COLOR_PAIRS < 6:
            self.log_attrs = {
                logging.DEBUG: (normal, normal),
                logging.INFO: (normal, normal),
                logging.WARNING: (normal, normal),
                logging.ERROR: (normal, normal),
                logging.CRITICAL: (normal, normal),
            }
        else:
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_RED)

            self.log_attrs = {
                logging.DEBUG: (curses.color_pair(1) | curses.A_DIM, normal | curses.A_DIM),
                logging.INFO: (curses.color_pair(2), normal),
                logging.WARNING: (curses.color_pair(3), normal),
                logging.ERROR: (curses.color_pair(4), normal),
                logging.CRITICAL: (curses.color_pair(5), normal),
            }

    def resize(self, nlines, ncols, begin_x, begin_y):
        self.window.resize(nlines, ncols)
        self.window.refresh()
        self.window.clear()
        self.posy = 0

    @contextlib.contextmanager
    def make_space(self, lines: int) -> ContextManager[Tuple[int, int]]:
        """
        Make space to append the given number of lines.

        Return the first and start lines where things can be written
        """
        # It seems impossible to write to the last character of the window without triggering scrolling
        # See: https://stackoverflow.com/questions/7063128/last-character-of-a-window-in-python-curses
        # See window.addch documentation
        maxy, maxx = self.window.getmaxyx()
        if self.posy + lines > maxy:
            self.window.scroll(self.posy + lines - maxy)
            self.window.move(maxy - lines, 0)
            yield maxy - lines, maxy
        else:
            self.window.move(self.posy, 0)
            yield self.posy, self.posy + lines
            self.posy = min(self.posy + lines, maxy)

    def write_log_entry(self, record, message: str):
        maxy, maxx = self.window.getmaxyx()

        with self.make_space(lines=1) as (first_line, last_line):
            dt = datetime.datetime.fromtimestamp(record.created)
            attr_head, attr_msg = self.log_attrs[record.levelno]

            self.window.addstr(first_line, 0, dt.strftime("%Y-%m-%d %H:%M:%S"), attr_head)
            self.window.addstr(first_line, 20, record.levelname[0], attr_head)

            message = message[:maxx - 22]
            if first_line == maxy - 1 and len(message) == maxx - 22:
                # We're writing to the last character of the screen, which
                # needs insstr, because addstr will move the cursor past the
                # end of the window and perform an unwanted scrolling
                # See: https://stackoverflow.com/questions/7063128/last-character-of-a-window-in-python-curses
                self.window.insstr(first_line, 22, message, attr_msg)
            else:
                self.window.addstr(first_line, 22, message, attr_msg)

        self.window.refresh()

    def write_exception(self, type, value, tb):
        import traceback
        maxy, maxx = self.window.getmaxyx()
        attr_head, attr_msg = self.log_attrs[logging.ERROR]
        lines = traceback.format_exception(type, value, tb)
        lines = lines[-(maxy - 1):]
        with self.make_space(len(lines)) as (first_line, last_line):
            for idx, line in enumerate(lines):
                self.window.insstr(first_line + idx, 0, line[:maxx], attr_head)
        self.window.refresh()


class CursesHandler(logging.Handler):
    def __init__(self, window: LogWindow, level=logging.NOTSET):
        super().__init__(level)
        self.window = window
        self.last_logging_exception = None
        self.history = collections.deque(maxlen=10000)

    def emit(self, record):
        try:
            message = record.getMessage()
            self.window.write_log_entry(record, message)
            self.history.append(self.format(record))
        except Exception:
            self.window.write_exception(*sys.exc_info())

    def dump(self, fname: str):
        with open(fname, "wt") as fd:
            for line in self.history:
                print(line, file=fd)

    def resize(self, nlines, ncols, begin_x, begin_y):
        self.window.resize(nlines, ncols, begin_x, begin_y)


class CommandPipe:
    def __init__(self, tui):
        self.rpipe, self.wpipe = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
        self.tui = tui

    def fileno(self):
        """
        Mock a file object for passing to selectors
        """
        return self.rpipe

    def on_event(self, events):
        # Flush the read endpoint
        while True:
            try:
                c = os.read(self.rpipe, 1)
            except BlockingIOError:
                break
            self.tui.on_command(c.decode())

    def post(self, cmd):
        os.write(self.wpipe, cmd.encode("ascii"))


class TUI(DballeWeb):
    def __init__(self, args):
        super().__init__(args)
        self.command_thread = None
        self.server = None
        self.stdscr = None
        self.log_handler = None
        self.command_pipe = CommandPipe(self)

    def start(self):
        logging.getLogger().setLevel(self.log_level)

        curses.wrapper(self.tui_main)

    def on_stdin(self, events):
        if self.log_handler.last_logging_exception is not None:
            raise RuntimeError("Error in logging") from self.log_handler.last_logging_exception
        maxy, maxx = self.stdscr.getmaxyx()

        key = self.stdscr.getch()
        if key in (ord('q'), ord('Q')):
            raise StopServer()
        elif key == ord('w'):
            webbrowser.open(self.start_url)
        elif key == ord('W'):
            webbrowser.open(self.forwarded_start_url)
        elif key == ord('l'):
            dt = datetime.datetime.now()
            dump_file = os.path.expanduser(dt.strftime("~/%Y%m%d-%H%M%S-dballe-web.log"))
            self.log_handler.dump(dump_file)
            log.warning("Logs dumped to %s", dump_file)
        # We don't get curses.KEY_RESIZE because in nonblocking mode, getch()
        # cannot handle SIGWINCH
        # elif key == curses.KEY_RESIZE:
        #     self.on_terminal_resized()

    def on_command(self, cmd: str):
        if cmd == 'W':
            self.on_terminal_resized()
        else:
            log.warning("Unknown command: %r", cmd)

    def on_terminal_resized(self):
        curses.endwin()
        self.stdscr.refresh()
        self.redraw()

        maxy, maxx = self.stdscr.getmaxyx()
        log_height = maxy - 4
        self.log_handler.resize(log_height - 2, maxx - 2, maxy - log_height + 1, 1)

    def redraw(self):
        maxy, maxx = self.stdscr.getmaxyx()

        self.stdscr.clear()

        # External border
        self.stdscr.border()

        # Horizontal separator line
        self.stdscr.addch(4, 0, curses.ACS_LTEE)
        self.stdscr.hline(4, 1, curses.ACS_HLINE, maxx - 1)
        self.stdscr.addch(4, maxx - 1, curses.ACS_RTEE)

        # Header information
        self.stdscr.addstr(1, 1, f"Running on {self.start_url} - 'q': quit, 'w': open browser, 'l': dump logs")
        self.stdscr.addstr(
                2, 1,
                f"Port forwarding command: ssh {getpass.getuser()}@{socket.getfqdn()} -NL 5000:localhost:{self.port}")
        self.stdscr.addstr(3, 1, f"Port forwarding URL: {self.forwarded_start_url}")

        self.stdscr.refresh()

    def tui_main(self, stdscr):
        from signal import signal, SIGWINCH

        def resize_handler(signum, frame):
            self.command_pipe.post("W")

        signal(SIGWINCH, resize_handler)

        self.stdscr = stdscr
        self.stdscr.timeout(0)
        curses.curs_set(0)

        # Setup logging to a window
        FORMAT = "%(asctime)-15s %(levelname)s %(name)s %(message)s"
        formatter = logging.Formatter(FORMAT, style='%')

        maxy, maxx = self.stdscr.getmaxyx()
        log_height = maxy - 4
        log_window = LogWindow(curses.newwin(log_height - 2, maxx - 2, maxy - log_height + 1, 1))

        self.log_handler = CursesHandler(log_window)
        self.log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.log_handler)

        self.server = self.start_flask()

        self.redraw()

        self.server.serve_forever(events=(
            (sys.stdin, selectors.EVENT_READ, self.on_stdin),
            (self.command_pipe, selectors.EVENT_READ, self.command_pipe.on_event),
        ))
