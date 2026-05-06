import json
import os
from datetime import datetime


class JsonDB:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        folder = os.path.dirname(self.file_path)

        if folder and not os.path.exists(folder):
            os.makedirs(folder)

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as file:
                json.dump([], file, indent=4)

    def _read(self) -> list:
        with open(self.file_path, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []

    def _write(self, data: list):
        with open(self.file_path, "w") as file:
            json.dump(data, file, indent=4)

    def _generate_id(self, data: list) -> int:
        if not data:
            return 1

        max_id = max(item.get("id", 0) for item in data)
        return max_id + 1

    def get_all(self) -> list:
        return self._read()

    def get_by_id(self, item_id: int) -> dict | None:
        data = self._read()

        for item in data:
            if item.get("id") == item_id:
                return item

        return None

    def create(self, item: dict) -> dict:
        data = self._read()
        new_item = {
            "id": self._generate_id(data),
            **item,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        data.append(new_item)
        self._write(data)

        return new_item

    def update(self, item_id: int, new_data: dict) -> dict | None:
        data = self._read()

        for index, item in enumerate(data):
            if item.get("id") == item_id:
                updated_item = {
                    **item,
                    **new_data,
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                data[index] = updated_item
                self._write(data)

                return updated_item
        return None

    def delete(self, item_id: int) -> bool:
        data = self._read()

        for item in data:
            if item.get("id") == item_id:
                data.remove(item)
                self._write(data)
                return True
        return False


products_db = JsonDB("db/products.json")
categories_db = JsonDB("db/categories.json")
