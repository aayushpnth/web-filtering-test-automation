#!/usr/bin/env python3
"""Entry point: python run.py --config config.yaml"""
import argparse
from url_filter_tester import run

def main():
    ap = argparse.ArgumentParser(description="URL filtering test harness (verdict collection only).")
    ap.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = ap.parse_args()
    paths = run(args.config)
    print("\nDone. Results:")
    for p in paths:
        print(" ", p)

if __name__ == "__main__":
    main()
