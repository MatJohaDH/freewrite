from textual.app import App, ComposeResult
from textual import events
from textual.widgets import Header, Footer, Static, Button, Markdown
from textual.containers import ScrollableContainer, Center
from time import monotonic
from textual.reactive import reactive


from collections import namedtuple
import sys

HourMinuteSecond = namedtuple('HourMinuteSecond', ['h', 'm', 's'], defaults=(0, 10, 0))

def tuple_time(time_tuple: tuple) -> float:
    """Calculate seconds from a H,M,S tuple."""
    return float(sum(value*unit for value, unit in zip(time_tuple, (3600, 60, 1))))


class ClockWork(Static):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    target = HourMinuteSecond(0, 10, 0)
    total = tuple_time(target)
    time = reactive(tuple_time(target))

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update time to current."""
        self.time = self.total - (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""

        minutes, seconds = divmod(abs(time), 60)
        hours, minutes = divmod(minutes, 60)

        minutes = f'{minutes:02,.0f}:' if minutes > 0 or hours > 0 else ''
        hours = f'{hours:02,.0f}:' if hours > 0 else ''

        sign = '-' if time < 0 else ''
        self.update(f"{sign}{hours}{minutes}{seconds:05.2f}")

        if time <= 0:
            stop_button = self.parent.parent.query_one("#stop", Button)
            stop_button.disabled = False


    def start(self) -> None:
        """Method to start (or resume) time updating."""
        self.start_time = monotonic()
        self.total = tuple_time(self.target)
        self.update_timer.resume()

    def stop(self) -> None:
        """Method to stop the time display updating."""
        self.update_timer.pause()
        self.total -= (monotonic() - self.start_time)
        self.time = self.total

    def reset(self) -> None:
        """Method to reset the time display to zero."""
        self.total = 0
        self.time = 0


class Countdown(Static):
    """Countdown that cannot be stopped until the time runs out."""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Method to register button clicks and start or stop the countdown."""
        button_id = event.button.id
        time_display = self.query_one(ClockWork)

        if button_id == "start":
            time_display.start()
            self.add_class("started")
            self.parent.parent.parent.mark.update('# Session in progress\n\nKeep typing until the timer reaches `0.00`.')
            event.button.disabled = True
            self.parent.parent.parent.text = ""
        elif button_id == "stop":
            time_display.stop()
            self.remove_class("started")
            time_display.update_timer.pause()
            self.parent.parent.parent.mark.update(self.parent.parent.parent.text)
            event.button.disabled = True

    def compose(self) -> ComposeResult:
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error", disabled=True)
        yield ClockWork()


class Freewrite(App):
    """A textual-based tool for structurng **freewriting***."""
    text = ""

    CSS = """Timer {
        layout: horizontal;
        height: 5;
        margin: 1;
        min-width: 50;
        padding: 1;
    }

    ClockWork {
        content-align: center middle;
        height: 3;
    }

    Button {
        width: 16;

    }

    #start {
        dock: left;
    }

    #stop {
        dock: right;
    }

    Markdown {
        align: center top;
        width: 60%;

    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        self.mark = Markdown(
            markdown=""" # Freewrite \n

            Write without stopping, backtracking or editing for 10 minutes.

            Press the *Start* button in the top-right corner to start.

            This text will be replaced with what you wrote once you hit the *Stop* button,
            which will be activated once the timer reaches `0.00`.
            """)
        yield ScrollableContainer(Countdown(), Center(self.mark))

    def on_key(self, event: events.Key) -> None:
        """Method that captures all keystrokes and stores all printable characters for printing out later."""
        if event.is_printable:
            self.text += event.character
            self.mark._markdown += event.character
        elif event.key == "tab":
            self.text += "\t"
        elif event.key == "enter":
            self.text += "\n\n"

def cli():
    freewriter = Freewrite()
    freewriter.run()

if __name__ == "__main__":
    cli()
