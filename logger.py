# logger.py: A simple, standardized logging utility for the T.H.E.A. project.
# It provides a singleton `logger` instance that writes structured, timestamped
# log entries to a file, including support for JSON data payloads and tracebacks.

import datetime
import json
import traceback


class SystemLogger:
    def __init__(self, log_file_path: str):
        self.log_file = open(log_file_path, "w", encoding="utf-8")

    def _log(self, level: str, component: str, message: str, data: any, **kwargs):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        log_entry = f"[{timestamp}] [{level.upper():<5}] [{component:<18}]"
        if message:
            log_entry += f" {message}"
        log_entry += "\n"

        if data is not None:
            try:
                # Use ensure_ascii=False to correctly log non-ASCII characters (e.g., Cyrillic).
                # `default=str` is a fallback for non-serializable objects like datetimes.
                data_str = json.dumps(data, indent=4, ensure_ascii=False, default=str)
            except (TypeError, OverflowError):
                data_str = str(data)

            indented_data = "\n".join(["    " + line for line in data_str.splitlines()])
            log_entry += indented_data + "\n"

        if kwargs.get("exc_info"):
            exc_info = traceback.format_exc()
            log_entry += "--- TRACEBACK ---\n"
            indented_traceback = "\n".join(
                ["    " + line for line in exc_info.splitlines()]
            )
            log_entry += indented_traceback + "\n"
            log_entry += "-----------------\n"

        self.log_file.write(log_entry)
        self.log_file.flush()

    def info(self, component: str, message: str = "", data: any = None):
        self._log("INFO", component, message, data)

    def warning(self, component: str, message: str = "", data: any = None):
        self._log("WARN", component, message, data)

    def error(self, component: str, message: str = "", data: any = None, **kwargs):
        self._log("ERROR", component, message, data, **kwargs)

    def close(self):
        if self.log_file and not self.log_file.closed:
            self.log_file.close()


from config import LOG_FILE_PATH

logger = SystemLogger(LOG_FILE_PATH)
