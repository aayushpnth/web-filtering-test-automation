"""Load configuration from YAML + environment. No secrets live in source."""
from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from typing import Any
import yaml

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

_ENV_PATTERN = re.compile(r"\$\{ENV:([A-Z0-9_]+)\}")


def _resolve_env(value: Any) -> Any:
    """Replace ${ENV:VAR} tokens with the value of that environment variable."""
    if isinstance(value, str):
        def repl(m):
            return os.environ.get(m.group(1), "")
        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value


@dataclass
class VendorConfig:
    name: str
    deployment: str
    settings: dict = field(default_factory=dict)   # host/token/etc, resolved from env


@dataclass
class Config:
    vendors: list[VendorConfig]
    corpus_path: str
    results_dir: str
    screenshot_dir: str
    syslog_bind_host: str
    syslog_bind_port: int
    page_timeout_seconds: int
    headless: bool

    @classmethod
    def load(cls, path: str = "config.yaml") -> "Config":
        with open(path, encoding="utf-8") as fh:
            raw = _resolve_env(yaml.safe_load(fh))
        vendors = [
            VendorConfig(name=v["name"], deployment=v.get("deployment", "unknown"),
                         settings={k: val for k, val in v.items() if k not in ("name", "deployment")})
            for v in raw.get("vendors", [])
        ]
        run = raw.get("run", {})
        sysl = raw.get("syslog", {})
        br = raw.get("browser", {})
        return cls(
            vendors=vendors,
            corpus_path=raw.get("corpus", {}).get("path", "corpus/urls.csv"),
            results_dir=run.get("results_dir", "results"),
            screenshot_dir=br.get("screenshot_dir", "screenshots"),
            syslog_bind_host=str(sysl.get("bind_host", "0.0.0.0")),
            syslog_bind_port=int(sysl.get("bind_port", 5514)),
            page_timeout_seconds=int(br.get("page_timeout_seconds", 30)),
            headless=bool(br.get("headless", True)),
        )
