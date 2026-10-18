"""``python -m generator.corpus --out DIR``: every document of both buckets as plain text.

An experiment that compares ways of handling the documents (raw, or scrubbed
by one tool or another) gives each the same text to start from, so the
format of a file is never what differs between them:

    DIR/<tenant>/<object key>.txt   the document's readable text
    DIR/index.json                  one entry per document: its tenant, id, key,
                                    label, true sensitivity, language, and the
                                    text file's path (null when the document has
                                    no readable text: an image, a scan, a corrupt
                                    file)

The text is what `textract.extract` reads, unchanged.
"""

import argparse
import csv
import json
from pathlib import Path

from generator.config import ROOT
from generator.ground_truth import TENANTS
from generator.textract import extract


def write(dataset: Path, out: Path) -> list[dict]:
    index = []
    for tenant in TENANTS:
        with open(dataset / "db" / "seed" / tenant / "documents.csv", newline="", encoding="utf-8") as handle:
            documents = list(csv.DictReader(handle))
        for document in documents:
            source = dataset / "bucket" / document["bucket"] / document["object_key"]
            text = extract(source.read_bytes(), document["object_key"])
            path = None
            if text is not None:
                path = f"{tenant}/{document['object_key']}.txt"
                target = out / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            index.append({
                "tenant": tenant, "document_id": document["document_id"], "object_key": document["object_key"],
                "label": document["sensitivity"], "language": document["language"], "path": path,
            })
    true = {}
    for item in json.loads((dataset / "ground_truth" / "manifest.json").read_text(encoding="utf-8")):
        for location in item["locations"]:
            if location["kind"] == "document":
                true[location["document_id"]] = location["true_sensitivity"]
    for entry in index:
        entry["true_sensitivity"] = true.get(entry["document_id"], entry["label"])
    (out / "index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return index


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m generator.corpus", description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True, help="where to write the text corpus")
    parser.add_argument("--dataset", type=Path, default=ROOT, help="the generated dataset (default: this repository)")
    args = parser.parse_args()
    index = write(args.dataset.resolve(), args.out.resolve())
    readable = sum(1 for entry in index if entry["path"])
    print(f"{readable} of {len(index)} documents written as text to {args.out}")


if __name__ == "__main__":
    main()
