"""List stock items from a CSV file."""

import argparse
import csv


def load(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return [{"name": row["name"], "qty": int(row["qty"])} for row in csv.DictReader(handle)]


def build_parser():
    parser = argparse.ArgumentParser(description="List stock items.")
    parser.add_argument("path", help="CSV file with name,qty columns")
    parser.add_argument("--sort", choices=["name", "qty"], default="name",
                        help="sort by name (A-Z) or by qty (largest first)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    items = load(args.path)
    if args.sort == "qty":
        items.sort(key=lambda item: (-item["qty"], item["name"]))
    else:
        items.sort(key=lambda item: item["name"])
    for item in items:
        print(f"{item['name']:<12}{item['qty']:>6}")


if __name__ == "__main__":
    main()
