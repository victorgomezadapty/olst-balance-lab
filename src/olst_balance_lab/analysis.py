"""Primary, sensitivity and descriptive analyses (ANALYSIS_PLAN.md sections 5 to 8)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import stats as S

ENDPOINTS = {
    "window_failure_share": "Share of 4 s windows not completed in one stable attempt",
    "tts_s": "Time to stability, s (first attempt per window)",
    "first_hold_s": "First attempt stable hold, s (0 if never stable)",
}


def primary_sample(windows: pd.DataFrame) -> pd.DataFrame:
    """All short windows of all participants (both groups did this task)."""
    return windows.copy()


def person_summary(w: pd.DataFrame, how: str = "median") -> pd.DataFrame:
    agg = np.median if how == "median" else np.mean
    g = w.groupby("pid")
    p = pd.DataFrame({
        "age_group": g["age_group"].first(),
        "self_assessment": g["self_assessment"].first(),
        "n_windows": g.size(),
        "window_failure_share": g["failure"].mean(),
        "tts_s": g["first_tts"].agg(lambda s: agg(s.dropna()) if s.notna().any() else np.nan),
        "first_hold_s": g["first_hold"].agg(lambda s: agg(s.dropna()) if s.notna().any() else np.nan),
        "attempts_per_window": g["n_attempts"].mean(),
    })
    return p.reset_index()


def compare(person: pd.DataFrame, label: str, cols=tuple(ENDPOINTS), seed=S.SEED) -> pd.DataFrame:
    rows = []
    for c in cols:
        r = S.boot_group_means(person, c, seed=seed)
        rows.append({"sample": label, "endpoint": c, "n_young": r["n_a"], "n_old": r["n_b"],
                     "young_mean": r["mean_a"], "young_ci95_low": r["ci_a"][0], "young_ci95_high": r["ci_a"][1],
                     "young_median": r["median_a"],
                     "old_mean": r["mean_b"], "old_ci95_low": r["ci_b"][0], "old_ci95_high": r["ci_b"][1],
                     "old_median": r["median_b"],
                     "diff_old_minus_young": r["diff"], "diff_ci95_low": r["diff_ci"][0], "diff_ci95_high": r["diff_ci"][1],
                     "welch_ci95_low": r["welch_ci"][0], "welch_ci95_high": r["welch_ci"][1], "welch_p": r["welch_p"]})
    return pd.DataFrame(rows)


def person_extra(a_short: pd.DataFrame) -> pd.DataFrame:
    g = a_short.groupby("pid")
    return pd.DataFrame({"age_group": g["age_group"].first(),
                         "naive_break_share": g["break_present"].mean(),
                         "early_touchdown_share": g["early_touchdown"].mean(),
                         "never_stable_share": g["never_stable"].mean(),
                         "n_attempts": g.size()}).reset_index()


def sensitivities(a: pd.DataFrame, w: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    s = a[(a["task"] == "short") & a["order_ok"]]
    # S1 attempt level, person cluster bootstrap
    rows = []
    for col, lab in [("tts", "tts_s"), ("hold", "hold_s_all_stable_attempts"), ("early_touchdown", "early_touchdown_share"),
                     ("break_present", "naive_break_share")]:
        d = s.assign(v=s[col].astype(float))
        r = S.boot_cluster_attempts(d, "v")
        rows.append({"sample": "S1 all valid short attempts, person cluster bootstrap", "endpoint": lab,
                     "n_young": r["n_a"], "n_old": r["n_b"], "young_mean": r["mean_a"], "young_ci95_low": r["ci_a"][0],
                     "young_ci95_high": r["ci_a"][1], "old_mean": r["mean_b"], "old_ci95_low": r["ci_b"][0],
                     "old_ci95_high": r["ci_b"][1], "diff_old_minus_young": r["diff"], "diff_ci95_low": r["diff_ci"][0],
                     "diff_ci95_high": r["diff_ci"][1]})
    s1 = pd.DataFrame(rows)
    out = [compare(person_summary(w, "mean"), "S2 person mean")]
    # S3 final attempt only (one per capture where flagged)
    f = s[s["is_attempt_final"]]
    pf = f.groupby("pid").agg(age_group=("age_group", "first"), tts_s=("tts", "median"),
                              first_hold_s=("hold", lambda x: np.median(np.nan_to_num(x.to_numpy(float), nan=0.0))),
                              window_failure_share=("never_stable", "mean")).reset_index()
    c3 = compare(pf, "S3 final attempt only (is_attempt_final), hold 0 if never stable, failure = never stable")
    out.append(c3)
    # S4 best hold
    pb = s.groupby("pid").agg(age_group=("age_group", "first"), first_hold_s=("hold", "max")).reset_index()
    out.append(compare(pb, "S4 best stable hold of any short attempt", cols=("first_hold_s",)))
    # S5 censored first attempts removed
    out.append(compare(person_summary(w[~w["first_censored"]]), "S5 windows with a censored first attempt removed"))
    # S6 versions V1 to V3 only
    out.append(compare(person_summary(w[w["version"].isin(["V1", "V2", "V3"])]), "S6 versions V1 to V3 only"))
    return s1, pd.concat(out, ignore_index=True)


def stance_foot(w: pd.DataFrame) -> pd.DataFrame:
    rows = []
    pl = person_summary(w[w["stance"] == "left"]).set_index("pid")
    pr = person_summary(w[w["stance"] == "right"]).set_index("pid")
    for grp in ["All", "Young", "Old"]:
        ids = pl.index if grp == "All" else pl.index[pl["age_group"] == grp]
        for c in ENDPOINTS:
            d = (pl.loc[ids, c] - pr.reindex(ids)[c]).to_numpy(float)
            r = S.boot_paired_mean(d)
            rows.append({"group": grp, "endpoint": c, "n_people": r["n"], "mean_left_base": float(np.nanmean(pl.loc[ids, c])),
                         "mean_right_base": float(np.nanmean(pr.reindex(ids)[c])), "mean_diff_left_minus_right": r["mean"],
                         "ci95_low": r["ci"][0], "ci95_high": r["ci"][1]})
    return pd.DataFrame(rows)


def self_assessment(person: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for grp in ["All", "Young", "Old"]:
        p = person if grp == "All" else person[person["age_group"] == grp]
        for c in ["window_failure_share", "first_hold_s"]:
            r = S.boot_spearman(p["self_assessment"], p[c])
            rows.append({"group": grp, "endpoint": c, "n_people": r["n"], "spearman_rho": r["rho"],
                         "ci95_low": r["ci"][0], "ci95_high": r["ci"][1]})
    return pd.DataFrame(rows)


MIN_CELL = 2  # cells describing fewer people than this are suppressed in public outputs


def self_assessment_cells(person: pd.DataFrame) -> pd.DataFrame:
    g = person.groupby(["age_group", "self_assessment"])
    t = g.agg(n_people=("pid", "size"), mean_failure_share=("window_failure_share", "mean"),
              median_first_hold_s=("first_hold_s", "median")).reset_index()
    t["suppressed"] = t["n_people"] < MIN_CELL
    t.loc[t["suppressed"], ["mean_failure_share", "median_first_hold_s"]] = np.nan
    return t


def long_trials(a: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    l = a[(a["task"] == "long") & a["order_ok"]]
    g = l.groupby("RADAR_capture")
    cap = pd.DataFrame({"pid": g["pid"].first(), "stance": g["stance"].first(), "n_attempts": g.size(),
                        "longest_hold_s": g["hold"].max(), "total_stable_s": g["hold"].sum(min_count=0),
                        "any_stable": g["never_stable"].apply(lambda x: (~x).any()),
                        "longest_is_censored": g.apply(lambda d: bool(d.loc[d["hold"].idxmax(), "censored"]) if d["hold"].notna().any() else False,
                                                       include_groups=False),
                        "window_s": g.apply(lambda d: float(d["MOCAP_End_Time"].iloc[0] - d["t_foot_up"].min()), include_groups=False)})
    cap["longest_hold_s"] = cap["longest_hold_s"].fillna(0.0)
    per = cap.groupby("pid").agg(n_captures=("n_attempts", "size"), median_longest_hold_s=("longest_hold_s", "median"),
                                 best_longest_hold_s=("longest_hold_s", "max"), median_total_stable_s=("total_stable_s", "median"),
                                 median_attempts=("n_attempts", "median")).reset_index()
    return cap.reset_index(), per


def long_summary(cap: pd.DataFrame, per: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, v in [("captures: attempts per capture", cap["n_attempts"]), ("captures: longest stable hold, s", cap["longest_hold_s"]),
                    ("captures: total stable time, s", cap["total_stable_s"]),
                    ("captures: foot lift to capture end, s", cap["window_s"]),
                    ("people: median longest hold, s", per["median_longest_hold_s"]),
                    ("people: best longest hold, s", per["best_longest_hold_s"])]:
        v = v.astype(float)
        person_level = name.startswith("people")  # min and max of person summaries are single people: suppressed
        rows.append({"measure": name, "n": int(v.notna().sum()), "median": v.median(), "p25": v.quantile(0.25),
                     "p75": v.quantile(0.75), "min": np.nan if person_level else v.min(),
                     "max": np.nan if person_level else v.max()})
    rows.append({"measure": "captures: one single attempt", "n": len(cap), "median": float((cap["n_attempts"] == 1).mean()),
                 "p25": np.nan, "p75": np.nan, "min": np.nan, "max": np.nan})
    rows.append({"measure": "captures: longest hold censored by capture end", "n": len(cap),
                 "median": float(cap["longest_is_censored"].mean()), "p25": np.nan, "p75": np.nan, "min": np.nan, "max": np.nan})
    return pd.DataFrame(rows)
