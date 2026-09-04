import logging
import os
from datetime import date


class DailyMessageRotatingFileHandler(logging.Handler):
    """Logging handler that writes to one file per day, starting a new file
    once the current one has reached `max_lines` lines.

    Files are named `<log_dir>/<YYYY-MM-DD>.1.log`, `.2.log`, ... On startup,
    if today's log file already exists, records are appended to it (the
    newest one, if it was rotated), continuing the line count already in
    that file rather than starting from scratch.
    """

    def __init__(self, log_dir: str, max_lines: int = 10_000, encoding: str = "utf-8"):
        super().__init__()
        self.log_dir = log_dir
        self.max_lines = max_lines
        self.encoding = encoding
        os.makedirs(self.log_dir, exist_ok=True)

        self._current_date: date = date.today()
        self._file_index = 0
        self._line_count = 0
        self._stream = None
        self._open_file(self._current_date, self._latest_index_for(self._current_date))

    def _build_filename(self, day: date, index: int) -> str:
        return os.path.join(self.log_dir, f"{day.isoformat()}.{index}.log")

    def _latest_index_for(self, day: date) -> int:
        """Returns the index of the most recent existing log file for `day`,
        or 1 if none exists yet."""
        index = 1
        while os.path.exists(self._build_filename(day, index + 1)):
            index += 1
        return index

    def _count_lines(self, path: str) -> int:
        if not os.path.exists(path):
            return 0
        with open(path, "r", encoding=self.encoding) as f:
            return sum(1 for _ in f)

    def _open_file(self, day: date, index: int):
        if self._stream:
            self._stream.close()

        self._current_date = day
        self._file_index = index
        filename = self._build_filename(day, index)
        self._line_count = self._count_lines(filename)
        self._stream = open(filename, "a", encoding=self.encoding)

    def emit(self, record):
        try:
            today = date.today()
            if today != self._current_date:
                self._open_file(today, self._latest_index_for(today))
            elif self._line_count >= self.max_lines:
                self._open_file(self._current_date, self._file_index + 1)

            text = self.format(record) + "\n"
            self._stream.write(text)
            self._stream.flush()
            self._line_count += text.count("\n")
        except Exception:
            self.handleError(record)

    def close(self):
        if self._stream:
            self._stream.close()
        super().close()


def get_logger(
    name: str,
    log_dir: str = "logs",
    max_lines: int = 10_000,
    level: int = logging.INFO,
) -> logging.Logger:
    """Returns the bot's logger, writing to daily, line-count-rotated log
    files under `log_dir` and mirroring output to the console.

    Safe to call multiple times; handlers are only attached once, and every
    call returns the same shared logger.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = DailyMessageRotatingFileHandler(log_dir=log_dir, max_lines=max_lines)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger
