"""Normalize a saved JSON response without making any network requests."""
import argparse
import hashlib
import json
from pathlib import Path
from evidence import adapt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    payload = json.loads(raw)
    metadata = payload.get("search_metadata", {}) if isinstance(payload, dict) else {}
    parameters = payload.get("search_parameters", {}) if isinstance(payload, dict) else {}
    provenance = {"source": "user-supplied saved response",
                  "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                  "provider_metadata": metadata, "search_parameters": parameters}
    result = adapt(payload, provenance)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"{result['state']}: {len(result['candidates'])} candidates written")


if __name__ == "__main__":
    main()
