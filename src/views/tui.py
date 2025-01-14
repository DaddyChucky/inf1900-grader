import os
import signal

from urwid import ExitMainLoop, Frame, MainLoop, Text, connect_signal

from src.views.panels.assemble import AssemblePanel
from src.views.panels.clone import ClonePanel
from src.views.panels.grade import GradePanel
from src.views.panels.mail import MailPanel
from src.views.panels.push import PushPanel
from src.views.widgets.form import DRAW_SIGNAL, QUIT_SIGNAL, SET_HEADER_TEXT_SIGNAL
from src.views.widgets.hydra import HydraWidget

palette = (
    ("blue_head", "dark blue", ""),
    ("red_head", "dark red", ""),
    ("header", "bold, underline, brown", ""),
    ("error", "bold, light red", ""),
    ("normal_box", "default", "default"),
    ("selected_box", "black", "light gray"),
    ("confirm_button", "yellow", "dark blue"),
    ("abort_button", "light red", "brown"),
    ("progress_low", "default", "yellow"),
    ("progress_hight", "default", "dark green"),
    ("helper_key", "bold", "default"),
    ("helper_text_brown", "black", "brown"),
    ("helper_text_red", "black", "dark red"),
    ("helper_text_green", "black", "dark green"),
    ("helper_text_light", "white", "dark blue"),
    ("popup", "white", "dark blue"),
)


class TUI:
    def __init__(self):
        self.keybind = {}

        self.main_helper_text = self.generate_helper_text([
            ("F10", "Quit", "helper_text_red"),
        ])

        self.subview_helper_text = self.generate_helper_text([
            ("F1", "Confirm", "helper_text_green"),
            ("F5", "Abort", "helper_text_brown"),
            ("F10", "Quit", "helper_text_red"),
            ("TAB", "Next", "helper_text_light"),
            ("S-TAB", "Previous", "helper_text_light")
        ])

        self.root = Frame(self.generate_main_view(),
                          Text(("header", ""), "center"),
                          self.main_helper_text)
        self.loop = MainLoop(self.root, palette, unhandled_input=self.unhandled_input)

        self.bind_global("f10", self.quit)
        self.handle_os_signals()

    def generate_main_view(self):
        main_view = HydraWidget("Welcome to INF1900 interactive grading tool!")

        subviews = (
            ("c", ClonePanel()),
            ("g", GradePanel()),
            ("a", AssemblePanel()),
            ("p", PushPanel()),
            ("m", MailPanel())
        )

        heads = []
        for letter, view, in subviews:
            hint = view.name
            connect_signal(view, QUIT_SIGNAL, self.display_main)
            connect_signal(view, SET_HEADER_TEXT_SIGNAL, self.set_header_text)
            connect_signal(view, DRAW_SIGNAL, self.draw_screen)
            heads.append(
                (letter, "blue_head", hint, self.display_subview, {"view": view, "hint": hint}))

        main_view.add_heads(heads)

        return main_view

    def start(self):
        try:
            self.loop.run()
        finally:
            self.loop.screen.stop()

    def unhandled_input(self, key):
        if key in self.keybind:
            self.keybind[key]()
            return None

    def bind_global(self, key, callback):
        self.keybind[key] = callback

    def set_header_text(self, string):
        self.root.header.set_text(string)

    def quit(self, *kargs):
        raise ExitMainLoop()

    def pause(self, *kargs):
        print("PAUSE")
        self.loop.stop()
        os.kill(os.getpid(), signal.SIGSTOP)
        self.loop.start()
        self.loop.draw_screen()

    def interrupt(self, *kargs):
        pass

    def handle_os_signals(self):
        signal.signal(signal.SIGQUIT, self.quit)
        signal.signal(signal.SIGTSTP, self.pause)
        signal.signal(signal.SIGINT, self.interrupt)

    @staticmethod
    def generate_helper_text(hints):
        markup = []
        for key, text, text_palette in hints:
            markup.extend((("helper_key", key), " ", (text_palette, text), " "))

        return Text(markup, align="center")

    def draw_screen(self):
        self.loop.draw_screen()

    def __change_view(self, view, hint):
        self.root.body = view if not hasattr(view, "root") else view.root
        self.set_header_text(hint)

    def display_subview(self, view, hint):
        self.root.footer = self.subview_helper_text
        self.__change_view(view, hint)

    def display_main(self, *kargs):
        self.root.footer = self.main_helper_text
        self.root.body = self.generate_main_view()  # to reload data from app state
        self.__change_view(self.root.body, "")
