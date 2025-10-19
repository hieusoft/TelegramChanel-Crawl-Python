# logger.py
from datetime import datetime
from pathlib import Path

class Logger:
    LEVELS = {
        "INFO": "[INFO]",
        "ERROR": "[ERROR]",
        "DEBUG": "[DEBUG]",
    }

    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)

    @staticmethod
    def _write_file(message: str):
        log_file = Logger.LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")

    @staticmethod
    def log(message: str, level: str = "INFO"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = Logger.LEVELS.get(level.upper(), "[INFO]")
        formatted = f"{now} {prefix} {message}"
        print(formatted)           # in ra console
        Logger._write_file(formatted)  # lưu vào file

    @staticmethod
    def info(message: str):
        Logger.log(message, "INFO")

    @staticmethod
    def error(message: str):
        Logger.log(message, "ERROR")

    @staticmethod
    def debug(message: str):
        Logger.log(message, "DEBUG")
