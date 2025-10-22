import json
from pathlib import Path

class Config:
    def __init__(self, config_path=None):
        """
        Load JSON config file
        :param config_path: path to config.json
        """
        if config_path is None:
            # Lấy thư mục chứa file này (config.py)
            config_path = Path(__file__).parent.parent / "config.json"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def get(self, key_path, default=None):
        """
        Lấy giá trị từ JSON theo path dạng 'telegram.api_id'
        """
        keys = key_path.split(".")
        data = self._data
        try:
            for key in keys:
                data = data[key]
            return data
        except (KeyError, TypeError):
            return default

    @property
    def data(self):
        return self._data


if __name__ == "__main__":
    config = Config()
    print(config.get("mysql.host"))
    print(config.get("translator.target_lang"))
    print(config.get("database.host"))
