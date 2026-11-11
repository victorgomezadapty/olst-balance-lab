"""Obtain the official files of PhysioNet olst-mocap-forceplate-radar 1.0 and verify every sha256.

Usage (from the project root):
    .venv/bin/python scripts/fetch_data.py                  # metadata, LICENSE.txt, SHA256SUMS.txt, README.txt
    .venv/bin/python scripts/fetch_data.py forceplate       # also short capture Raw/ForcePlate CSVs (about 2.2 GB, local only)
    .venv/bin/python scripts/fetch_data.py forceplate-all   # every force-plate CSV (about 3.5 GB)

Files already present are only verified. The two metadata tables are copied (never moved) from a
local verified cache when one exists, otherwise downloaded. Downloads go to a .part file, are
checked against the official SHA256SUMS.txt, and only then renamed. Any mismatch stops the script.
Only force-plate CSVs are downloaded from Raw/; no MOCAP, QTM, radar or Figures files.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from olst_balance_lab import data as D  # noqa: E402

LOCAL_CACHE = {D.DEMO_FILE: Path("/workspace/dsverify/olst_demo.csv"), D.ATT_FILE: Path("/workspace/dsverify/olst_att.csv")}


def download(url: str, target: Path, sha: str, nbytes: int | None = None) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=180) as resp, open(part, "wb") as fh:
                while chunk := resp.read(1 << 20):
                    fh.write(chunk)
            break
        except OSError:
            if attempt == 2:
                raise
    D.verify_file(part, sha, nbytes)
    part.rename(target)


def ensure(name: str, dep_path: str, sha: str, nbytes: int | None) -> None:
    target = D.RAW_DIR / name
    if not target.exists():
        src = LOCAL_CACHE.get(name)
        if src is not None and src.is_file() and D.sha256_of(src) == sha:
            shutil.copy2(src, target)  # copy, never move the cache
        else:
            print(f"downloading {dep_path}")
            download(D.FILES_URL + dep_path, target, sha, nbytes)
    D.verify_file(target, sha, nbytes)


def fetch_forceplate(sums: dict[str, str], workers: int = 12, short_only: bool = True) -> int:
    todo = []
    files = {k: v for k, v in D.fp_files_from_sums(sums).items() if not short_only or "_MNTR" in k}
    for dep_path, sha in files.items():
        target = D.RAW_DIR / dep_path
        if target.exists():
            D.verify_file(target, sha)
        else:
            todo.append((dep_path, sha, target))
    print(f"force-plate files to download: {len(todo)}")

    def job(t):
        download(D.FILES_URL + t[0], t[2], t[1])
        return t[0]

    with ThreadPoolExecutor(workers) as ex:
        for i, _ in enumerate(ex.map(job, todo), 1):
            if i % 50 == 0:
                print(f"  {i}/{len(todo)}", flush=True)
    return len(files)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="metadata", choices=["metadata", "forceplate", "forceplate-all"])
    args = ap.parse_args()
    D.RAW_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if not (D.RAW_DIR / D.SUMS_FILE).exists():
            download(D.FILES_URL + D.SUMS_FILE, D.RAW_DIR / D.SUMS_FILE, D.SUMS_SHA256, D.SUMS_BYTES)
        sums = D.official_sums()
        for name, (dep_path, sha, nbytes) in D.EXPECTED.items():
            if sums.get(dep_path) != sha:
                raise D.IntegrityError(f"{dep_path}: pinned hash not in {D.SUMS_FILE}")
            ensure(name, dep_path, sha, nbytes)
        ensure(D.README_FILE, D.README_FILE, D.README_SHA256, None)
        res = D.verify_raw()
        if args.mode != "metadata":
            n = fetch_forceplate(sums, short_only=args.mode == "forceplate")
            print(f"ok {n} force-plate CSVs verified")
    except D.IntegrityError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    for name, v in res.items():
        print(f"ok {name} {v['bytes']} bytes sha256 {v['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
