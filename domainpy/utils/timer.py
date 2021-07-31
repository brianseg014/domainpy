from __future__ import annotations

import time
import typing


class TimerError(Exception):
    pass


class Timer:
    def __init__(self) -> None:
        self.start_time: typing.Optional[int] = None
        self.end_time: typing.Optional[int] = None

    @property
    def elapsed_time_ns(self) -> int:
        if self.start_time is None:
            raise TimerError("timer not running")

        if self.end_time is None:
            raise TimerError("timer still running")

        return self.end_time - self.start_time

    def __enter__(self) -> Timer:
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()

    def start(self) -> None:
        if self.start_time is not None:
            raise TimerError("timer already started")

        self.start_time = time.process_time_ns()

    def stop(self) -> None:
        if self.start_time is None:
            raise TimerError("timer not running")

        if self.end_time is not None:
            raise TimerError("timer already stopped")

        self.end_time = time.process_time_ns()
