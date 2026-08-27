"""Load the URL test corpus. The corpus file itself is git-ignored."""
from __future__ import annotations
import csv
from dataclasses import dataclass


@dataclass
class TestUrl:
    url: str
    type: str        # BENIGN | MALICIOUS
    expected_category: str = ""   # optional ground truth for benign


def load_corpus(path: str) -> list[TestUrl]:
    items: list[TestUrl] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            items.append(TestUrl(
                url=row["url"].strip(),
                type=row["type"].strip().upper(),
                expected_category=row.get("expected_category", "").strip(),
            ))
    return items
