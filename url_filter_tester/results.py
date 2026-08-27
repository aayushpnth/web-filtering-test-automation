"""Write per-URL run results to a CSV. This CSV is the input to a separate scoring step."""
from __future__ import annotations
import csv
import os

FIELDS = ["vendor", "deployment", "url", "type", "expected_category",
          "loaded", "blocked", "has_log", "action", "category",
          "malicious_category_logged", "screenshot", "detail"]


class ResultWriter:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._fh = open(path, "w", newline="", encoding="utf-8")
        self._w = csv.DictWriter(self._fh, fieldnames=FIELDS)
        self._w.writeheader()

    def write(self, row: dict) -> None:
        self._w.writerow({k: row.get(k, "") for k in FIELDS})

    def close(self) -> None:
        self._fh.close()
