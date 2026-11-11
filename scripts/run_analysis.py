"""Run the full OLST Balance Lab analysis offline from the verified local deposit files.

Usage (from the project root):
    .venv/bin/python scripts/run_analysis.py

Stops with an error if any official file differs from its pinned size or sha256. Writes tables/
(aggregates), figures/ (PNG and WebP), results/summary.json and RESULTS.md. The force-plate check
runs only when every short capture force-plate CSV is present and verified; otherwise it is skipped
and recorded as skipped.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from olst_balance_lab import analysis as A  # noqa: E402
from olst_balance_lab import audit as AU  # noqa: E402
from olst_balance_lab import data as D  # noqa: E402
from olst_balance_lab import events as E  # noqa: E402
from olst_balance_lab import figures as F  # noqa: E402
from olst_balance_lab import forceplate as FP  # noqa: E402
from olst_balance_lab.report import write_results_md  # noqa: E402

TABLES, FIGS, RES = ROOT / "tables", ROOT / "figures", ROOT / "results"


def r(x, k=4):
    if isinstance(x, (list, tuple)):
        return [r(v, k) for v in x]
    if isinstance(x, dict):
        return {kk: r(v, k) for kk, v in x.items()}
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, str) or x is None:
        return x
    return None if np.isnan(x) else round(float(x), k)


def table_dict(t: pd.DataFrame, key: str) -> dict:
    return {row[key]: {c: r(row[c]) for c in t.columns if c != key and c != "sample"} for _, row in t.iterrows()}


def compute(run_forceplate: bool = True):
    hashes = D.verify_raw()
    demo_raw, att = D.load_raw()
    demo = D.prepare_demo(demo_raw)
    a = E.assign_windows(E.prepare_attempts(att, demo))
    cmp_df, flags, facts = AU.audit(demo_raw, demo, a)
    complete = AU.completeness_table(a)
    w = E.window_table(a)
    prim_w = A.primary_sample(w)
    person = A.person_summary(prim_w)
    prim = A.compare(person, "primary")
    extra = A.person_extra(a[(a["task"] == "short") & a["order_ok"]])
    extra_cmp = A.compare(extra, "primary sample, attempt shares per person",
                          cols=("early_touchdown_share", "naive_break_share", "never_stable_share"))
    s1, sens = A.sensitivities(a, w)
    stance = A.stance_foot(prim_w)
    selfa = A.self_assessment(person)
    cells = A.self_assessment_cells(person)
    long_cap, long_per = A.long_trials(a)
    long_sum = A.long_summary(long_cap, long_per)
    apw = prim_w.groupby("age_group")["n_attempts"].agg(["mean", "median", "max", "size"]).reset_index()
    fp = {"status": "skipped", "reason": "not run"}
    fp_feat = fp_sum = None
    if run_forceplate:
        sums = D.official_sums()
        short_caps = sorted(a.loc[a["task"] == "short", "RADAR_capture"].unique())
        avail = FP.available(short_caps, sums)
        listed = [k for k in D.fp_files_from_sums(sums) if "_MNTR" in k]
        local_ok = all((D.RAW_DIR / k).exists() for k in listed)
        no_fp_in_deposit = sorted(c for c in short_caps if not all(str(FP.fp_path(c, sd).relative_to(D.RAW_DIR)) in sums for sd in ("left", "right")))
        if local_ok and len(avail) + len(no_fp_in_deposit) == len(short_caps):
            fp_feat, used = FP.attempt_features(a[a["task"] == "short"], sums)
            fp_sum = FP.summarise(fp_feat)
            fp = {"status": "run", "captures": len(used), "files": 2 * len(used), "attempts": int(len(fp_feat)),
                  "people": int(fp_feat["pid"].nunique()), "short_captures_without_forceplate_in_deposit": no_fp_in_deposit}
        else:
            fp = {"status": "skipped", "reason": f"only {len(avail)} of {len(short_caps)} short captures have verified force-plate files locally"}
    return locals()


def main() -> None:
    for p in (TABLES, FIGS, RES):
        p.mkdir(exist_ok=True)
    for old in list(TABLES.glob("*.csv")) + list(FIGS.glob("*.png")) + list(FIGS.glob("*.webp")):
        old.unlink()  # generated outputs only; data/raw is never touched
    c = compute()
    samples = pd.DataFrame([
        {"sample": "primary: all short windows", "windows": len(c["prim_w"]), "people": c["person"]["pid"].nunique(),
         "young_people": int((c["person"].age_group == "Young").sum()), "old_people": int((c["person"].age_group == "Old").sum()),
         "young_windows": int((c["prim_w"].age_group == "Young").sum()), "old_windows": int((c["prim_w"].age_group == "Old").sum()),
         "attempts": int((c["a"].task == "short").sum())},
    ])
    outs = [("t01_card_vs_files.csv", c["cmp_df"]), ("t02_audit_flags.csv", c["flags"]), ("t03_event_completeness.csv", c["complete"]),
            ("t04_primary_sample.csv", samples), ("t05_primary_young_vs_old.csv", c["prim"]),
            ("t06_attempt_shares_per_person.csv", c["extra_cmp"]), ("t07_sensitivity_attempt_level_S1.csv", c["s1"]),
            ("t08_sensitivity_person_level.csv", c["sens"]), ("t09_stance_foot.csv", c["stance"]),
            ("t10_self_assessment_spearman.csv", c["selfa"]), ("t11_self_assessment_cells.csv", c["cells"]),
            ("t12_long_old_only_descriptive.csv", c["long_sum"]), ("t13_attempts_per_window.csv", c["apw"])]
    if c["fp_sum"] is not None:
        outs.append(("t14_forceplate_check.csv", c["fp_sum"]))
    for name, t in outs:
        t.to_csv(TABLES / name, index=False, float_format="%.6g")
    made = []
    made += F.fig_audit(c["facts"], c["complete"], FIGS / "fig01_deposit_audit.png")
    made += F.fig_schematic(FIGS / "fig02_protocol_schematic.png")
    made += F.fig_primary(c["person"], c["prim"], FIGS / "fig03_primary_young_vs_old.png")
    made += F.fig_sensitivity(c["prim"], c["sens"], c["s1"], FIGS / "fig04_sensitivity.png")
    made += F.fig_stance_self(c["stance"], c["cells"], FIGS / "fig05_stance_and_self_rating.png")
    made += F.fig_long(c["long_cap"], FIGS / "fig06_long_old_only.png")
    if c["fp_sum"] is not None:
        made += F.fig_forceplate(c["fp_sum"], FIGS / "fig07_forceplate_check.png")
    prim = c["prim"]
    summary = {
        "project": D.SHORT_NAME, "package": D.PACKAGE, "status": "local draft, not published",
        "dataset": {"title": D.DATASET_TITLE, "physionet_slug": D.SLUG, "version": D.VERSION, "page": D.PAGE_URL,
                    "version_doi": D.VERSION_DOI, "concept_doi": D.CONCEPT_DOI, "published": D.PUBLISHED, "creators": D.CREATORS,
                    "citation": D.DATASET_CITATION, "physionet_citation": D.PHYSIONET_CITATION, "access": "open access",
                    "license": D.LICENSE_NAME, "license_contradiction": False, "files_verified": c["hashes"]},
        "companion_paper": D.COMPANION,
        "environment": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
        "audit": {"facts": r(c["facts"]), "flags": {row.flag: {"severity": row.severity, "item": row.item, "finding": row.finding}
                                                     for row in c["flags"].itertuples()}},
        "primary_sample": {"definition": ("all short captures (MNTRL, MNTRR) of all 32 participants, attempts grouped into cued 4 s "
                                          "windows (new window when the foot lifts at least 2.0 s after the previous attempt ended); "
                                          "one summary per person over all their short windows; Old minus Young"),
                           "windows": len(c["prim_w"]), "people": int(c["person"]["pid"].nunique()),
                           "young_people": int(prim.n_young.iloc[0]), "old_people": int(prim.n_old.iloc[0]),
                           "young_windows": int((c["prim_w"].age_group == "Young").sum()),
                           "old_windows": int((c["prim_w"].age_group == "Old").sum())},
        "ci_method": "percentile bootstrap, persons resampled within group, 5000 resamples, seed 20261111; Welch t interval as a check",
        "primary": table_dict(prim, "endpoint"),
        "attempt_shares_per_person": table_dict(c["extra_cmp"], "endpoint"),
        "sensitivity_S1_attempt_level": table_dict(c["s1"], "endpoint"),
        "sensitivity_person_level": {lab: table_dict(g, "endpoint") for lab, g in c["sens"].groupby("sample", sort=False)},
        "stance_foot": {f"{row.group}|{row.endpoint}": {k: r(getattr(row, k)) for k in ["n_people", "mean_left_base", "mean_right_base",
                        "mean_diff_left_minus_right", "ci95_low", "ci95_high"]} for row in c["stance"].itertuples()},
        "self_assessment_descriptive": {f"{row.group}|{row.endpoint}": {k: r(getattr(row, k)) for k in ["n_people", "spearman_rho",
                                        "ci95_low", "ci95_high"]} for row in c["selfa"].itertuples()},
        "long_old_only_descriptive": {row.measure: {k: r(getattr(row, k)) for k in ["n", "median", "p25", "p75", "min", "max"]}
                                      for row in c["long_sum"].itertuples()},
        "attempts_per_window": {row.age_group: {"mean": r(row.mean), "median": r(row.median), "max": r(row.max), "windows": r(row.size)}
                                for row in c["apw"].itertuples()},
        "forceplate": {**c["fp"], **({"summary": [{k: r(v) for k, v in row.items()} for row in c["fp_sum"].to_dict("records")]}
                                     if c["fp_sum"] is not None else {})},
        "figure_titles": F.TITLES, "figure_footer": F.FOOTER,
        "outputs": {"tables": sorted(p.name for p in TABLES.glob("*.csv")), "figures": sorted(p.name for p in made)},
    }
    (RES / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_results_md(summary, ROOT / "RESULTS.md")
    log = [f"python {platform.python_version()} pandas {pd.__version__} numpy {np.__version__}"]
    log += [f"verified {k} sha256 {v['sha256']}" for k, v in c["hashes"].items()]
    log += [f"forceplate {c['fp']}", f"tables {len(outs)}", f"figures {len(made)}"]
    (RES / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
