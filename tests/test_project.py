"""Integrity, definition, sample, output, license, privacy and copy tests for OLST Balance Lab."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from olst_balance_lab import analysis as A  # noqa: E402
from olst_balance_lab import data as D  # noqa: E402
from olst_balance_lab import events as E  # noqa: E402

DOCS = ["README.md", "RESULTS.md", "DATA_LICENSE.md", "PROVENANCE.md", "PORTFOLIO_BRIEF.md", "ANALYSIS_PLAN.md", "DISCUSSION.md",
        "LICENSE", "requirements.txt", ".gitignore"]
DASHES = ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2015", "\u2212", "-" * 2]
FORBIDDEN_NAMES = ["optimo", "malqa", "riyadh"]
FORBIDDEN_CLAIMS = ["we replicate", "successfully replicated", "outperform", "beats the", "better than the paper",
                    "kaggle.com", "uploaded to kaggle", "vercel.app", "diagnoses fall risk", "predicts falls",
                    "clinical cut-off is", "clinical cutoff is", "proves", "equivalent to the clinical"]


@pytest.fixture(scope="module")
def summary():
    return json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def frames():
    demo_raw, att = D.load_raw()
    demo = D.prepare_demo(demo_raw)
    a = E.assign_windows(E.prepare_attempts(att, demo))
    return demo, a, E.window_table(a)


# Integrity

def test_pinned_hashes_match_official_sums_and_brief():
    sums = D.official_sums()
    assert sums["Metadata/Participant_Demographics.csv"] == "92d8b45db27dd28af0949c735dc83027d4ec89ff76b21f3e7a403cd569cb83f5"
    assert sums["Metadata/OLST_Attempts.csv"] == "fdfed70659a153f0be3a19edaf8c810ddb9d91c29f1668b8b95f80e192e3253b"
    assert sums["LICENSE.txt"] == "9a78e7f22742dde9f66ae235ec793ba2212019dc4d0ced75c4da09ced0b35fb2"
    for name, (dep, sha, _) in D.EXPECTED.items():
        assert sums[dep] == sha


def test_local_files_verify_with_sizes():
    res = D.verify_raw()
    assert res[D.DEMO_FILE]["bytes"] == 984
    assert res[D.ATT_FILE]["bytes"] == 133530
    assert sum(1 for _ in open(D.RAW_DIR / D.ATT_FILE, encoding="utf-8-sig")) == 1242


def test_license_file_is_cc_by_4(tmp_path):
    text = (D.RAW_DIR / "LICENSE.txt").read_text(encoding="utf-8")
    assert "Attribution 4.0 International" in text
    assert "NonCommercial" not in text


def _copy_raw(tmp_path):
    for n in [D.SUMS_FILE, *D.EXPECTED]:
        shutil.copy2(D.RAW_DIR / n, tmp_path / n)


def test_tampered_metadata_is_refused(tmp_path):
    _copy_raw(tmp_path)
    p = tmp_path / D.ATT_FILE
    b = bytearray(p.read_bytes())
    b[-2] = ord("9") if b[-2] != ord("9") else ord("8")
    p.write_bytes(bytes(b))
    with pytest.raises(D.IntegrityError):
        D.verify_raw(tmp_path)
    with pytest.raises(D.IntegrityError):
        D.load_raw(tmp_path)


def test_truncated_or_missing_file_is_refused(tmp_path):
    _copy_raw(tmp_path)
    p = tmp_path / D.DEMO_FILE
    p.write_bytes(p.read_bytes()[:-10])
    with pytest.raises(D.IntegrityError, match="size"):
        D.verify_raw(tmp_path)
    (tmp_path / D.DEMO_FILE).unlink()
    with pytest.raises(D.IntegrityError, match="missing"):
        D.verify_raw(tmp_path)


def test_tampered_sums_file_is_refused(tmp_path):
    _copy_raw(tmp_path)
    p = tmp_path / D.SUMS_FILE
    p.write_text(p.read_text().replace("fdfed706", "00000000"))
    with pytest.raises(D.IntegrityError):
        D.verify_raw(tmp_path)


def test_html_shells_would_be_refused(tmp_path):
    shell = Path("/workspace/dsverify/olst_OLST_Attempts.csv")
    if not shell.exists():
        pytest.skip("no html shell on this machine")
    _copy_raw(tmp_path)
    shutil.copy2(shell, tmp_path / D.ATT_FILE)
    with pytest.raises(D.IntegrityError):
        D.verify_raw(tmp_path)


# Event definitions

def test_time_to_stability_definition():
    assert np.allclose(E.time_to_stability([10.0, 5.0], [10.6, np.nan])[:1], [0.6])
    assert np.isnan(E.time_to_stability([5.0], [np.nan])[0])


def test_stable_hold_definition():
    h = E.stable_hold([11.0, 11.0, np.nan], [14.0, np.nan, np.nan], [15.0, 15.2, 15.0])
    assert h[0] == pytest.approx(3.0)       # t_break present
    assert h[1] == pytest.approx(4.2)       # held to t_end
    assert np.isnan(h[2])                   # never stable: nothing invented


def test_events_on_real_rows(frames):
    _, a, _ = frames
    r = a[a["OLST_attempt_id"] == "01_MNTRL_RR_V1_an1"].iloc[0]
    assert r["tts"] == pytest.approx(11.19 - 10.22)
    assert r["hold"] == pytest.approx(14.28 - 11.19)
    r = a[a["OLST_attempt_id"] == "01_MNTRL_RR_V1_an3"].iloc[0]
    assert r["hold"] == pytest.approx(30.2 - 27.03) and bool(r["censored"])
    assert a["tts"].notna().sum() == a["t_stable"].notna().sum()
    assert (a["tts"].dropna() >= 0).all() and (a["hold"].dropna() >= 0).all()


def test_window_rule_toy():
    toy = pd.DataFrame({"RADAR_capture": ["01_MNTRL_RR_V1"] * 4, "an": [1, 2, 3, 4], "task": "short",
                        "t_foot_up": [10.0, 12.0, 18.0, 26.0], "t_end": [11.5, 14.8, 22.8, 30.0], "MOCAP_Start_Time": 8.0,
                        "never_stable": [False, False, False, False]})
    w = E.assign_windows(toy)
    assert w["window"].tolist() == [1, 1, 2, 3]
    assert w["early_touchdown"].tolist() == [True, False, False, False]


# Primary sample

def test_primary_sample_is_short_only_both_groups(frames, summary):
    demo, a, w = frames
    prim = A.primary_sample(w)
    caps = set(prim["capture"])
    assert all(c.split("_")[1] in E.SHORT_CODES for c in caps)
    assert prim["pid"].nunique() == 32
    assert set(prim["age_group"]) == {"Young", "Old"}
    assert summary["primary_sample"]["young_people"] == 15 and summary["primary_sample"]["old_people"] == 17
    assert summary["primary_sample"]["windows"] == len(prim)
    assert len(prim) == a[a["task"] == "short"]["window_id"].nunique()


def test_long_trials_never_in_primary(frames):
    _, a, w = frames
    long_caps = set(a.loc[a["task"] == "long", "RADAR_capture"])
    assert long_caps and not (long_caps & set(w["capture"]))
    assert set(a.loc[a["task"] == "long", "age_group"]) == {"Old"}


def test_failure_definition(frames):
    _, _, w = frames
    assert ((w["n_attempts"] >= 2) | w["any_never_stable"]).equals(w["failure"])


def test_person_summary_one_row_per_person(frames):
    _, _, w = frames
    p = A.person_summary(w)
    assert p["pid"].is_unique and len(p) == 32


# Numeric lock: documents agree with results

def test_readme_reports_primary_numbers(summary):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    p = summary["primary"]
    for key, scale, fmt in [("window_failure_share", 100, "{:.1f}%"), ("tts_s", 1, "{:.2f}"), ("first_hold_s", 1, "{:.2f}")]:
        for k in ["young_mean", "old_mean"]:
            assert fmt.format(p[key][k] * scale) in readme, (key, k)


def test_audit_counts(summary):
    f = summary["audit"]["facts"]
    assert f["n_participants"] == 32 and f["n_attempts"] == 1241 and f["n_captures"] == 334
    assert f["finals_true"] == 314 and f["id_max"] == 56 and f["n_under_18"] == 0
    assert f["capture_12_MNTRL_V2_present"] is True
    assert f["participant_12_MNTRL_versions_in_attempts"] == ["V2", "V3"]


# Outputs

def test_outputs_exist(summary):
    for t in summary["outputs"]["tables"]:
        assert (ROOT / "tables" / t).stat().st_size > 0
    figs = summary["outputs"]["figures"]
    assert len([x for x in figs if x.endswith(".png")]) >= 6
    for name in figs:
        assert (ROOT / "figures" / name).stat().st_size > 5000
        if name.endswith(".png"):
            assert (ROOT / "figures" / name).with_suffix(".webp").exists()


def test_outputs_are_aggregate(summary):
    for p in (ROOT / "tables").glob("*.csv"):
        t = pd.read_csv(p)
        assert len(t) <= 60, p.name
        assert not {"pid", "Participant_ID", "OLST_attempt_id", "RADAR_capture"} & set(t.columns), p.name
    text = (ROOT / "RESULTS.md").read_text(encoding="utf-8")
    assert not re.search(r"\b\d{2}_(MNTR|TRLG)[LR]_RR_V\d_an\d+\b", text)


# License, privacy, copy

def test_gitignore_keeps_metadata_but_not_raw_signals():
    gi = (ROOT / ".gitignore").read_text()
    assert "data/raw/Raw/" in gi and ".venv/" in gi
    for name in ["Participant_Demographics.csv", "OLST_Attempts.csv", "LICENSE.txt", "SHA256SUMS.txt"]:
        assert name not in gi
    if (ROOT / ".git").exists():
        files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
        assert not any(f.startswith("data/raw/Raw/") or f.endswith((".qtm", ".mat")) for f in files)
        assert "data/raw/README.txt" not in files


def test_no_remote_configured():
    if not (ROOT / ".git").exists():
        pytest.skip("no git repo")
    out = subprocess.run(["git", "remote"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    assert out == ""


def our_texts():
    files = [ROOT / n for n in DOCS]
    files += sorted((ROOT / "src").rglob("*.py")) + sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "tables").glob("*.csv"))
    files += [ROOT / "results" / "summary.json"]
    return {str(p.relative_to(ROOT)): p.read_text(encoding="utf-8") for p in files}


def test_no_long_dashes_or_double_hyphens():
    for name, text in our_texts().items():
        for d in DASHES:
            assert d not in text, (name, repr(d))


def test_no_forbidden_names_claims_or_emails():
    for name, text in our_texts().items():
        low = text.lower()
        for w in FORBIDDEN_NAMES + FORBIDDEN_CLAIMS:
            assert w not in low, (name, w)
        emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
        assert not [e for e in emails if not e.startswith("victorgomeztrainer")], (name, emails)


def test_docs_cite_required_sources():
    for n in ["README.md", "DATA_LICENSE.md"]:
        t = (ROOT / n).read_text(encoding="utf-8")
        for s in ["10.13026/46hn-6b25", "10.1038/s41597-026-06831-1", "10.1038/s44360-026-00096-z", "CC BY 4.0"]:
            assert s in t, (n, s)
    t = (ROOT / "DATA_LICENSE.md").read_text(encoding="utf-8")
    assert "10.13026/70xa-vm53" in t and "CC BY-NC-ND 4.0" in t and "do not endorse" in t
    assert "Daniel Copeland, Evan Linton, Xiang Zhang, Hector Lugaro," in t


def test_chart_titles_clean():
    from olst_balance_lab import figures as F
    for t in list(F.TITLES.values()) + [F.FOOTER]:
        for d in DASHES:
            assert d not in t
