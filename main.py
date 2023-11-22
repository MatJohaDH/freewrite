from textual.app import App, ComposeResult
from textual import events
from textual.widgets import Header, Footer, Static, Button, Markdown
from textual.containers import ScrollableContainer
from time import monotonic
from textual.reactive import reactive


class ClockWork(Static):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update time to current."""
        self.time = self.total + (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")
        if minutes >= 10:
            stop_button = self.parent.parent.query_one("#stop", Button)
            stop_button.disabled = False

    def start(self) -> None:
        """Method to start (or resume) time updating."""
        self.start_time = monotonic()
        self.update_timer.resume()

    def stop(self) -> None:
        """Method to stop the time display updating."""
        self.update_timer.pause()
        self.total += monotonic() - self.start_time
        self.time = self.total

    def reset(self) -> None:
        """Method to reset the time display to zero."""
        self.total = 0
        self.time = 0


class Timer(Static):
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        time_display = self.query_one(ClockWork)

        if button_id == "start":
            time_display.start()
            self.add_class("started")
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
    text = ""

    CSS_PATH = "layout.css"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        self.mark = Markdown(markdown="mark")
        yield ScrollableContainer(Timer(), self.mark)

    def on_key(self, event: events.Key) -> None:
        if event.is_printable:
            self.text += event.character
            self.mark._markdown += event.character
        elif event.key == "tab":
            self.text += "\t"
        elif event.key == "enter":
            self.text += "\n\n"


if __name__ == "__main__":
    app = Freewrite()
    app.run()
