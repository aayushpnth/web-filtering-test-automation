# URL Filtering Test Harness

An open, vendor neutral automation tool for testing how web security products (on premise NGFW, SSE, and FWaaS) handle a corpus of URLs. For each URL it drives a real browser, decides whether the URL was allowed or blocked, captures a screenshot, and correlates the vendor syslog to record the action and category. The result is a per URL verdict CSV.

This tool only **collects verdicts**. Turning those verdicts into scores is a separate step, so nothing here depends on any particular scoring scheme.

It ships with synthetic sample data and contains **no vendor hosts, credentials, corpus, or baseline data**. Every sensitive value is loaded at runtime from a git ignored config and environment variables, so the repository is safe to publish.

## What it does

1. Reads a corpus of test URLs (benign and malicious), each with an optional expected category.
2. For every configured vendor and deployment, opens each URL in a headless browser.
3. Classifies the outcome:
   * page renders normally, treated as allowed
   * navigation fails with a connection reset, timeout, or DNS error, treated as a blocked or silently dropped request
   * a block page is detected in the page content, treated as blocked
4. Listens for syslog and correlates each URL to the log line for its domain to capture the vendor action and category.
5. Writes one results CSV per vendor with the full per URL verdict, plus a screenshot per URL.

## Why it is built this way

Different products log differently and some block silently, so a single browser signal or a single log signal is not enough. Capturing both the browser outcome and the correlated log entry gives a complete, auditable verdict for every URL that you can later score however you like.

## Architecture

```
corpus (URLs)  ->  runner  ->  per URL:
                                  browser visit  -> allowed / blocked + screenshot
                                  syslog correlate -> action + category + has_log
                             ->  results/<vendor>_<deployment>.csv
```

Modules:

```
url_filter_tester/
  config.py            loads config.yaml + resolves ${ENV:...} secrets
  corpus.py            loads the URL test corpus
  browser.py           Playwright driver, allow/block detection, screenshots
  syslog_collector.py  UDP syslog listener + per URL correlation (override friendly)
  results.py           writes the per URL verdict CSV
  runner.py            orchestrates a full run
run.py                 command line entry point
```

## Requirements

* Python 3.10 or newer
* Playwright with the Chromium browser installed

## Install

```bash
git clone https://github.com/<your-org>/url-filtering-test-harness.git
cd url-filtering-test-harness
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Configure

1. Copy the templates and fill in your own values:

   ```bash
   cp config.example.yaml config.yaml
   cp .env.example .env
   ```

2. Put credentials and hosts in `.env` only. The config references them as `${ENV:VAR}`, so no secret is ever written into a tracked file.

3. Point `corpus.path` at your own URL list. Keep the corpus and any baseline under the git ignored `corpus/` and `baselines/` folders.

`config.yaml`, `.env`, `corpus/`, `baselines/`, `results/`, and `screenshots/` are all git ignored, so real data cannot be committed by accident.

## Run

```bash
python run.py --config config.yaml
```

Results are written to `results/<vendor>_<deployment>.csv`. Try it against the bundled synthetic corpus first by setting `corpus.path` to `examples/sample_corpus.csv`.

## Adapting to your products

* **Block page detection:** extend `BLOCK_PAGE_MARKERS` in `browser.py` with the phrases your products show on their block pages.
* **Log parsing:** override `parse_entry` and `MALICIOUS_CATEGORY_KEYWORDS` in `syslog_collector.py` to match your product log format. Some products delay log forwarding, so tune the wait in `runner.py` accordingly.

## License

MIT.

## Disclaimer

Use this tool only against systems and URLs you are authorized to test. Handle malicious test URLs in an isolated environment. The authors are not responsible for misuse.
