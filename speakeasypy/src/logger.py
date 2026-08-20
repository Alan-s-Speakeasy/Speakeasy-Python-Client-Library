import logging
import os
from datetime import date


class DailyMessageRotatingFileHandler(logging.Handler):
    """Logging handler that writes to one file per day, starting a new file
    once the current one has received `max_messages` records.

    Files are named `<log_dir>/<YYYY-MM-DD>.log` for the first file of the
    day, then `<log_dir>/<YYYY-MM-DD>.1.log`, `.2.log`, ... for subsequent
    rotations on the same day.
    """

    def __init__(self, log_dir: str, max_messages: int = 1000, encoding: str = "utf-8"):
        super().__init__()
        self.log_dir = log_dir
        self.max_messages = max_messages
        self.encoding = encoding
        os.makedirs(self.log_dir, exist_ok=True)

        self._current_date = None
        self._file_index = 0
        self._message_count = 0
        self._stream = None
        self._open_new_file(reset_index=True)

    def _build_filename(self) -> str:
        date_str = self._current_date.isoformat()
        suffix = "" if self._file_index == 0 else f".{self._file_index}"
        return os.path.join(self.log_dir, f"{date_str}{suffix}.log")

    def _open_new_file(self, reset_index: bool = False):
        if self._stream:
            self._stream.close()

        self._current_date = date.today()
        self._message_count = 0
        if reset_index:
            self._file_index = 0
            # Avoid overwriting a non-empty file left over from a previous run today.
            while os.path.exists(self._build_filename()) and os.path.getsize(self._build_filename()) > 0:
                self._file_index += 1

        self._stream = open(self._build_filename(), "a", encoding=self.encoding)

    def emit(self, record):
        try:
            if date.today() != self._current_date:
                self._open_new_file(reset_index=True)
            elif self._message_count >= self.max_messages:
                self._file_index += 1
                self._open_new_file()

            self._stream.write(self.format(record) + "\n")
            self._stream.flush()
            self._message_count += 1
        except Exception:
            self.handleError(record)

    def close(self):
        if self._stream:
            self._stream.close()
        super().close()


def get_logger(
    name: str,
    log_dir: str = "logs",
    max_messages: int = 1000,
    level: int = logging.INFO,
) -> logging.Logger:
    """Returns a logger that writes to daily, message-count-rotated log
    files under `log_dir`, and mirrors output to the console.

    Safe to call multiple times with the same `name`; handlers are only
    attached once.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = DailyMessageRotatingFileHandler(log_dir=log_dir, max_messages=max_messages)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger
