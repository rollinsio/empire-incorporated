"""``python -m generator [--out DIR]``: rebuild the whole dataset."""

import argparse
import json
from pathlib import Path

from generator.build import GENERATED, build
from generator.config import ROOT


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m generator", description="Rebuild the Empire Incorporated test dataset.")
    parser.add_argument("--out", type=Path, default=ROOT,
                        help=f"output root (default: the repository). Replaces {', '.join(GENERATED)} under it.")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    summary = build(out)
    print(json.dumps({tenant: {k: info[k] for k in ("documents", "bytes", "german_documents")} for tenant, info in summary["tenants"].items()}
                     | {"questions": summary["questions"]["by_category"]}, indent=2))


if __name__ == "__main__":
    main()
