"""Deposit metadata, pinned hashes and verified loading for PhysioNet olst-mocap-forceplate-radar 1.0.

Every load re-checks the size and sha256 of the official files. A mismatch raises IntegrityError;
nothing is ever corrected silently.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
FP_DIR = RAW_DIR / "Raw" / "ForcePlate"

SHORT_NAME = "OLST Balance Lab"
PACKAGE = "olst_balance_lab"
SLUG = "olst-mocap-forceplate-radar"
VERSION = "1.0"
DATASET_TITLE = ("Multimodal Synchronized Motion Capture, Force Plate, and Radar Dataset of the One-Legged Stand Test "
                 "for Fall-Risk Assessment")
CREATORS = ["Daniel Copeland", "Evan Linton", "Xiang Zhang", "Hector Lugaro", "Buntoku Mori", "Brian Anthony"]
VERSION_DOI = "10.13026/46hn-6b25"
CONCEPT_DOI = "10.13026/70xa-vm53"
PUBLISHED = "2026-01-25"
PAGE_URL = f"https://physionet.org/content/{SLUG}/{VERSION}/"
FILES_URL = f"https://physionet.org/files/{SLUG}/{VERSION}/"
LICENSE_NAME = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
DATASET_CITATION = ("Copeland, D., Linton, E., Zhang, X., Lugaro, H., Mori, B., and Anthony, B. (2026). " + DATASET_TITLE +
                    " (version 1.0). PhysioNet. RRID:SCR_007345. https://doi.org/10.13026/46hn-6b25")
PHYSIONET_CITATION = ("Pollard, T., et al. (2026). PhysioNet as a global platform for biomedical research. Nature Health. "
                      "https://doi.org/10.1038/s44360-026-00096-z")
COMPANION = {
    "citation": ("Copeland D, Zhang X, Linton E, Mori B, Lugaro H, Anthony BW. One-Legged Stand Test: Synchronized Motion "
                 "Capture, Force Plate, and Radar Dataset for Fall-Risk. Scientific Data. Published 25 Feb 2026."),
    "doi": "10.1038/s41597-026-06831-1",
    "license": "CC BY-NC-ND 4.0",
    "use": "cited only; no text, tables, figures, code or coefficients reused",
}

SUMS_FILE = "SHA256SUMS.txt"
SUMS_SHA256 = "ac177ee0c4771088d722d0ff03df5a9bcc0968d2546089d587d07e4750e00da8"
SUMS_BYTES = 178551
DEMO_FILE = "Participant_Demographics.csv"
ATT_FILE = "OLST_Attempts.csv"
# name in data/raw -> (path inside the deposit, sha256, bytes)
EXPECTED = {
    "LICENSE.txt": ("LICENSE.txt", "9a78e7f22742dde9f66ae235ec793ba2212019dc4d0ced75c4da09ced0b35fb2", 14842),
    DEMO_FILE: ("Metadata/Participant_Demographics.csv",
                "92d8b45db27dd28af0949c735dc83027d4ec89ff76b21f3e7a403cd569cb83f5", 984),
    ATT_FILE: ("Metadata/OLST_Attempts.csv", "fdfed70659a153f0be3a19edaf8c810ddb9d91c29f1668b8b95f80e192e3253b", 133530),
}
README_FILE = "README.txt"  # local only (gitignored); used for the audit
README_SHA256 = "92f9d309d028b987f6f4fced8d89b24cf22ccedadc00ef29abe9d28f82a2d9db"


class IntegrityError(RuntimeError):
    """Raised when a file differs from its pinned official size or sha256."""


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_file(path: Path, sha256: str, nbytes: int | None = None) -> dict:
    path = Path(path)
    if not path.is_file():
        raise IntegrityError(f"missing file: {path}")
    size = path.stat().st_size
    if nbytes is not None and size != nbytes:
        raise IntegrityError(f"size mismatch for {path.name}: {size} bytes, expected {nbytes}")
    got = sha256_of(path)
    if got != sha256:
        raise IntegrityError(f"sha256 mismatch for {path.name}: {got}, expected {sha256}")
    return {"bytes": size, "sha256": got}


def parse_sums(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            out[parts[1]] = parts[0]
    return out


def official_sums(raw_dir: Path = RAW_DIR) -> dict[str, str]:
    verify_file(raw_dir / SUMS_FILE, SUMS_SHA256, SUMS_BYTES)
    return parse_sums((raw_dir / SUMS_FILE).read_text(encoding="utf-8"))


def verify_raw(raw_dir: Path = RAW_DIR) -> dict:
    """Check the sums file, then the license and the two metadata tables against it and the pinned values."""
    sums = official_sums(raw_dir)
    res = {SUMS_FILE: {"bytes": SUMS_BYTES, "sha256": SUMS_SHA256}}
    for name, (dep_path, sha, nbytes) in EXPECTED.items():
        if sums.get(dep_path) != sha:
            raise IntegrityError(f"pinned hash for {dep_path} disagrees with {SUMS_FILE}")
        res[name] = verify_file(raw_dir / name, sha, nbytes)
    return res


def load_raw(raw_dir: Path = RAW_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Verified load of the two official metadata tables (unchanged values; columns renamed in memory only)."""
    verify_raw(raw_dir)
    demo = pd.read_csv(raw_dir / DEMO_FILE, encoding="utf-8-sig")
    att = pd.read_csv(raw_dir / ATT_FILE, encoding="utf-8-sig")
    return demo, att


DEMO_RENAME = {"Participant_ID": "pid", "Age": "age", "Gender (1=M,2=F)": "gender", "Height (in)": "height_in",
               "Weight (lb)": "weight_lb", "BMI": "bmi", "Balance Self Assessment": "self_assessment", "Age_Group": "age_group"}


def prepare_demo(demo: pd.DataFrame) -> pd.DataFrame:
    d = demo.rename(columns=DEMO_RENAME).copy()
    d["height_cm"] = d["height_in"] * 2.54
    d["weight_kg"] = d["weight_lb"] * 0.45359237
    d["bmi_recomputed"] = d["weight_kg"] / (d["height_cm"] / 100) ** 2
    return d


def fp_files_from_sums(sums: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in sums.items() if k.startswith("Raw/ForcePlate/")}
