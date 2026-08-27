"""
Orchestrate a run: for each vendor, visit every corpus URL, correlate the log,
and record the verdict. Produces one results CSV per vendor.

This harness only COLLECTS verdicts. Scoring is a separate concern/tool.
"""
from __future__ import annotations
import os
import time

from .config import Config
from .corpus import load_corpus
from .browser import visit
from .syslog_collector import SyslogCollector
from .results import ResultWriter


def run(config_path: str = "config.yaml") -> list[str]:
    cfg = Config.load(config_path)
    corpus = load_corpus(cfg.corpus_path)

    collector = SyslogCollector(cfg.syslog_bind_host, cfg.syslog_bind_port)
    collector.start()
    out_paths: list[str] = []
    try:
        for vendor in cfg.vendors:
            out = os.path.join(cfg.results_dir, f"{vendor.name}_{vendor.deployment}.csv")
            writer = ResultWriter(out)
            shot_dir = os.path.join(cfg.screenshot_dir, vendor.name)
            print(f"[{vendor.name}/{vendor.deployment}] testing {len(corpus)} URLs")
            for item in corpus:
                res = visit(item.url, shot_dir, headless=cfg.headless, timeout_s=cfg.page_timeout_seconds)
                time.sleep(0.2)  # allow the log to arrive; tune per environment
                corr = collector.correlate(item.url)
                writer.write({
                    "vendor": vendor.name,
                    "deployment": vendor.deployment,
                    "url": item.url,
                    "type": item.type,
                    "expected_category": item.expected_category,
                    "loaded": res.loaded,
                    "blocked": res.blocked,
                    "has_log": corr.has_log,
                    "action": corr.action,
                    "category": corr.category,
                    "malicious_category_logged": corr.is_malicious_category,
                    "screenshot": res.screenshot_path,
                    "detail": res.detail,
                })
            writer.close()
            out_paths.append(out)
            print(f"  -> wrote {out}")
    finally:
        collector.stop()
    return out_paths
