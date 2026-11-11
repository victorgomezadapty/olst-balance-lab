"""Optional force-plate check of the official labels (ANALYSIS_PLAN.md section 9).

Uses only Raw/ForcePlate CSVs, each verified against the official SHA256SUMS.txt before use.
Short captures only. Output is aggregate; per attempt features stay in memory.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data as D
from . import stats as S

SMOOTH_N = 60        # 50 ms at 1200 Hz
ROLL_N = 300         # 250 ms
STAY_N = 600         # 0.5 s
MIN_FZ_N = 20.0
UNLOAD_FRAC = 0.05


def fp_path(capture: str, side: str):
    pid, code, _, ver = capture.split("_")
    return D.FP_DIR / pid / f"{pid}_{code}_FP_{ver}_{side}.csv"


def available(captures, sums) -> list[str]:
    ok = []
    for c in captures:
        paths = [fp_path(c, s) for s in ("left", "right")]
        keys = [str(p.relative_to(D.RAW_DIR)) for p in paths]
        if all(p.exists() for p in paths) and all(k in sums for k in keys):
            ok.append(c)
    return ok


def load_plate(path, sums, verify=True) -> pd.DataFrame:
    if verify:
        D.verify_file(path, sums[str(path.relative_to(D.RAW_DIR))])
    return pd.read_csv(path, usecols=["time", "Force_Z", "COP_X", "COP_Y"])


def cop_speed(df: pd.DataFrame) -> np.ndarray:
    t = df["time"].to_numpy(float)
    x = pd.Series(df["COP_X"].to_numpy(float)).rolling(SMOOTH_N, center=True, min_periods=1).mean().to_numpy()
    y = pd.Series(df["COP_Y"].to_numpy(float)).rolling(SMOOTH_N, center=True, min_periods=1).mean().to_numpy()
    sp = np.hypot(np.gradient(x, t), np.gradient(y, t))
    sp[df["Force_Z"].to_numpy(float) < MIN_FZ_N] = np.nan
    return sp


def _med(t, v, t0, t1):
    m = (t >= t0) & (t < t1)
    return float(np.nanmedian(v[m])) if m.sum() > 10 and np.isfinite(v[m]).sum() > 10 else np.nan


def onset_time(t, speed, t_up, t_end):
    roll = pd.Series(speed).rolling(ROLL_N, min_periods=ROLL_N // 2).mean().to_numpy()
    m = (t >= t_up) & (t <= t_end)
    if m.sum() < STAY_N:
        return np.nan
    thr = np.nanmedian(roll[m])
    idx = np.where(m)[0]
    below = roll[idx] < thr
    run = 0
    for k, b in enumerate(below):
        run = run + 1 if b else 0
        if run >= STAY_N:
            return float(t[idx[k - STAY_N + 1]])
    return np.nan


def attempt_features(a_short: pd.DataFrame, sums: dict, verify=True) -> pd.DataFrame:
    rows = []
    caps = available(a_short["RADAR_capture"].unique(), sums)
    for cap in caps:
        rows_c = a_short[a_short["RADAR_capture"] == cap]
        stance_side = rows_c["stance"].iloc[0]
        lifted_side = "right" if stance_side == "left" else "left"
        st = load_plate(fp_path(cap, stance_side), sums, verify)
        li = load_plate(fp_path(cap, lifted_side), sums, verify)
        t = st["time"].to_numpy(float)
        sp = cop_speed(st)
        fz_s, fz_l = st["Force_Z"].to_numpy(float), li["Force_Z"].to_numpy(float)
        for r in rows_c.itertuples():
            rec = {"pid": r.pid, "age_group": r.age_group, "capture": cap, "complete": bool(pd.notna(r.t_stable) and pd.notna(r.t_break))}
            if pd.notna(r.t_stable):
                on = onset_time(t, sp, r.t_foot_up, r.t_end)
                rec["onset_minus_stable_s"] = on - r.t_stable if np.isfinite(on) else np.nan
            if rec["complete"]:
                m = (t >= r.t_stable) & (t < r.t_break)
                rec["unloaded"] = bool(np.median(fz_l[m]) < UNLOAD_FRAC * np.median(fz_s[m])) if m.sum() > 10 else np.nan
                rec["cop_fu"] = _med(t, sp, r.t_foot_up, r.t_stable)
                rec["cop_stable"] = _med(t, sp, r.t_stable, r.t_break)
                rec["cop_fd"] = _med(t, sp, r.t_break, r.t_end)
            rows.append(rec)
    f = pd.DataFrame(rows)
    if len(f) and "cop_stable" in f:
        ok = f[["cop_fu", "cop_stable", "cop_fd"]].notna().all(axis=1)
        f["cop_agree"] = np.where(ok, (f["cop_stable"] < f["cop_fu"]) & (f["cop_stable"] < f["cop_fd"]), np.nan)
        f["cop_lower_than_fu"] = np.where(f[["cop_fu", "cop_stable"]].notna().all(axis=1), f["cop_stable"] < f["cop_fu"], np.nan)
        f["within_0_5s"] = np.where(f["onset_minus_stable_s"].notna(), f["onset_minus_stable_s"].abs() <= 0.5, np.nan)
    return f, caps


def summarise(f: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for grp in ["All", "Young", "Old"]:
        d = f if grp == "All" else f[f["age_group"] == grp]
        for col, lab in [("unloaded", "lifted plate unloaded during labelled stable phase"),
                         ("cop_agree", "stance COP speed lowest in labelled stable phase"),
                         ("cop_lower_than_fu", "stance COP speed lower than foot up phase (added after plan)"),
                         ("within_0_5s", "force-plate onset within 0.5 s of t_stable")]:
            x = d[["pid", col]].dropna()
            x = x.assign(v=x[col].astype(float), age_group="g")
            if len(x) == 0:
                continue
            rng = np.random.default_rng(S.SEED)
            sums_ = x.groupby("pid")["v"].agg(["sum", "size"])
            bs = []
            for _ in range(2000):
                k = rng.integers(0, len(sums_), len(sums_))
                bs.append(sums_["sum"].to_numpy()[k].sum() / sums_["size"].to_numpy()[k].sum())
            lo, hi = S.pct_ci(bs)
            rows.append({"group": grp, "check": lab, "attempts": len(x), "people": int(x["pid"].nunique()),
                         "share": float(x["v"].mean()), "ci95_low": lo, "ci95_high": hi})
        o = d["onset_minus_stable_s"].dropna()
        rows.append({"group": grp, "check": "force-plate onset minus t_stable, s (median; p25 to p75 in CI columns)",
                     "attempts": int(o.size), "people": int(d.loc[o.index, "pid"].nunique()),
                     "share": float(o.median()) if o.size else np.nan,
                     "ci95_low": float(o.quantile(0.25)) if o.size else np.nan, "ci95_high": float(o.quantile(0.75)) if o.size else np.nan})
        for c in ["cop_fu", "cop_stable", "cop_fd"]:
            if c in d:
                v = d[c].dropna()
                rows.append({"group": grp, "check": f"median stance COP speed, {c[4:]} phase, mm/s", "attempts": int(v.size),
                             "people": int(d.loc[v.index, "pid"].nunique()), "share": float(v.median()) if v.size else np.nan,
                             "ci95_low": float(v.quantile(0.25)) if v.size else np.nan, "ci95_high": float(v.quantile(0.75)) if v.size else np.nan})
    return pd.DataFrame(rows)
