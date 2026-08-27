"""
Minimal syslog UDP listener + correlation helper.

Runs a background listener that captures incoming syslog lines, then lets the
runner correlate a URL/domain to the log entries observed around that time to
extract the vendor action and category. Products vary widely in log format, so
parse_entry is intentionally a simple, override-friendly stub.
"""
from __future__ import annotations
import socket
import threading
import time
from dataclasses import dataclass, field


@dataclass
class LogEntry:
    received_at: float
    raw: str


@dataclass
class Correlation:
    has_log: bool
    action: str          # e.g. "block" | "allow" | "unknown"
    category: str        # vendor category string, or ""
    is_malicious_category: bool


class SyslogCollector:
    def __init__(self, bind_host: str = "0.0.0.0", bind_port: int = 5514):
        self.bind_host = bind_host
        self.bind_port = bind_port
        self._entries: list[LogEntry] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _serve(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.bind_host, self.bind_port))
        sock.settimeout(0.5)
        while not self._stop.is_set():
            try:
                data, _ = sock.recvfrom(65535)
            except socket.timeout:
                continue
            with self._lock:
                self._entries.append(LogEntry(time.time(), data.decode("utf-8", "replace")))
        sock.close()

    def snapshot(self) -> list[LogEntry]:
        with self._lock:
            return list(self._entries)

    # -- override these two for your product's log format --

    MALICIOUS_CATEGORY_KEYWORDS = ("malware", "phishing", "malicious", "command-and-control",
                                   "botnet", "spyware", "exploit")

    def parse_entry(self, raw: str) -> Correlation:
        low = raw.lower()
        action = "block" if any(k in low for k in ("block", "deny", "drop", "reset")) else \
                 ("allow" if any(k in low for k in ("allow", "permit", "accept")) else "unknown")
        category = ""
        for kw in self.MALICIOUS_CATEGORY_KEYWORDS:
            if kw in low:
                category = kw
                break
        return Correlation(has_log=True, action=action, category=category,
                           is_malicious_category=bool(category))

    def correlate(self, url: str) -> Correlation:
        """Find the most recent log line mentioning the URL's domain."""
        domain = url.split("://")[-1].split("/")[0].lower()
        for entry in reversed(self.snapshot()):
            if domain and domain in entry.raw.lower():
                return self.parse_entry(entry.raw)
        return Correlation(has_log=False, action="unknown", category="", is_malicious_category=False)
