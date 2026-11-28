"""List stock items from a CSV file."""

import argparse
import csv
import json


def load(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return [{"name": row["name"], "qty": int(row["qty"])} for row in csv.DictReader(handle)]


def build_parser():
    parser = argparse.ArgumentParser(description="List stock items.")
    parser.add_argument("path", help="CSV file with name,qty columns")
    parser.add_argument("--sort", choices=["name", "qty"], default="name",
                        help="sort by name (A-Z) or by qty (largest first)")
    parser.add_argument("--limit", type=int, default=None, help="show at most this many items")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="output format")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    items = load(args.path)
    if args.limit is not None:
        items = items[:args.limit]
    if args.sort == "qty":
        items.sort(key=lambda item: (-item["qty"], item["name"]))
    else:
        items.sort(key=lambda item: item["name"])
    if args.format == "json":
        print(json.dumps(items))
        return
    for item in items:
        print(f"{item['name']:<12}{item['qty']:>6}")


if __name__ == "__main__":
    main()
