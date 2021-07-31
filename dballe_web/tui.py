from typing import Tuple, ContextManager
import contextlib
import webbrowser
import selectors
import datetime
import logging
import getpass
import socket
import curses
import sys
from .ui import DballeWeb
from .application import StopServer


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


class CursesHandler(logging.Handler):
    def __init__(self, window: LogWindow, level=logging.NOTSET):
        super().__init__(level)
        self.window = window

    def emit(self, record):
        try:
            message = record.getMessage()
            self.window.write_log_entry(record, message)
        except Exception:
            raise
            # TODO: if a problem happens here, figure out how to log it / show it
            # self.handleError(record)


class TUI(DballeWeb):
    def __init__(self, args):
        super().__init__(args)
        self.command_thread = None
        self.server = None
        self.stdscr = None

    def start(self):
        logging.getLogger().setLevel(self.log_level)

        curses.wrapper(self.tui_main)

    def on_stdin(self, events):
        maxy, maxx = self.stdscr.getmaxyx()

        key = self.stdscr.getch()
        if key in (ord('q'), ord('Q')):
            raise StopServer()
        elif key == ord('w'):
            webbrowser.open(self.start_url)
        elif key == ord('W'):
            webbrowser.open(self.forwarded_start_url)
        elif key == curses.KEY_RESIZE:
            # TODO: handle resize
            pass
        # TODO: add a key to dump logs

    def tui_main(self, stdscr):
        # TODO: handle window resize
        maxy, maxx = stdscr.getmaxyx()
        self.stdscr = stdscr
        self.stdscr.timeout(0)
        curses.curs_set(0)

        # External border
        self.stdscr.border()

        # Horizontal separator line
        self.stdscr.addch(4, 0, curses.ACS_LTEE)
        self.stdscr.hline(4, 1, curses.ACS_HLINE, maxx - 1)
        self.stdscr.addch(4, maxx - 1, curses.ACS_RTEE)

        # TODO: show menu
        # TODO: handle tracebacks from code
        #        - turn log window into a class, with methods to add log lines
        #          and also a method to add a traceback?
        #        - make it scroll up/down with arrows?

        # Setup logging to a window
        FORMAT = "%(asctime)-15s %(levelname)s %(name)s %(message)s"
        formatter = logging.Formatter(FORMAT, style='%')

        log_height = maxy - 4
        log_window = LogWindow(curses.newwin(log_height - 2, maxx - 2, maxy - log_height + 1, 1))

        handler = CursesHandler(log_window)
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)

        self.server = self.start_flask()

        # Header information
        stdscr.addstr(1, 1, f"Running on {self.start_url} (Press 'q' to quit))")
        stdscr.addstr(
                2, 1,
                f"Port forwarding command: ssh {getpass.getuser()}@{socket.getfqdn()} -NL 5000:localhost:{self.port}")
        stdscr.addstr(3, 1, f"Port forwarding URL: {self.forwarded_start_url}")

        stdscr.refresh()

        self.server.serve_forever(events=(
            (sys.stdin, selectors.EVENT_READ, self.on_stdin),
        ))
