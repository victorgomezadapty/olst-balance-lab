"""Attempt level event definitions and cue window assignment (ANALYSIS_PLAN.md sections 3 and 4)."""
from __future__ import annotations

import numpy as np
import pandas as pd

CENSOR_TOL_S = 0.005
WINDOW_GAP_S = 2.0
SHORT_CODES = ("MNTRL", "MNTRR")
LONG_CODES = ("TRLGL", "TRLGR")


def parse_capture(capture: pd.Series) -> pd.DataFrame:
    parts = capture.str.split("_", expand=True)
    out = pd.DataFrame({"pid": parts[0].astype(int), "code": parts[1], "modality": parts[2], "version": parts[3]},
                       index=capture.index)
    out["task"] = np.where(out["code"].isin(SHORT_CODES), "short", np.where(out["code"].isin(LONG_CODES), "long", "other"))
    out["stance"] = out["code"].str[-1].map({"L": "left", "R": "right"})
    return out


def time_to_stability(t_foot_up, t_stable):
    """t_stable minus t_foot_up; NaN when t_stable is missing (never invented)."""
    return np.asarray(t_stable, float) - np.asarray(t_foot_up, float)


def stable_hold(t_stable, t_break, t_end):
    """t_break minus t_stable if t_break is present, else t_end minus t_stable; NaN if never stable."""
    t_stable, t_break, t_end = (np.asarray(x, float) for x in (t_stable, t_break, t_end))
    stop = np.where(np.isnan(t_break), t_end, t_break)
    return stop - t_stable


def prepare_attempts(att: pd.DataFrame, demo: pd.DataFrame) -> pd.DataFrame:
    a = att.copy()
    a = pd.concat([a, parse_capture(a["RADAR_capture"])], axis=1)
    a = a.merge(demo[["pid", "age", "gender", "age_group", "self_assessment"]], on="pid", how="left", validate="many_to_one")
    a = a.sort_values(["RADAR_capture", "an"]).reset_index(drop=True)
    a["never_stable"] = a["t_stable"].isna()
    a["break_present"] = a["t_break"].notna()
    a["censored"] = np.isclose(a["t_end"], a["MOCAP_End_Time"], atol=CENSOR_TOL_S, rtol=0)
    seq = a[["t_foot_up", "t_stable", "t_break", "t_end"]].to_numpy(float)
    ok = np.ones(len(a), bool)
    for i in range(3):
        for j in range(i + 1, 4):
            both = ~np.isnan(seq[:, i]) & ~np.isnan(seq[:, j])
            ok &= ~both | (seq[:, i] <= seq[:, j])
    a["order_ok"] = ok
    a["tts"] = time_to_stability(a["t_foot_up"], a["t_stable"])
    a["hold"] = stable_hold(a["t_stable"], a["t_break"], a["t_end"])
    a.loc[~a["order_ok"], ["tts", "hold"]] = np.nan
    a["attempt_len"] = a["t_end"] - a["t_foot_up"]
    return a


def assign_windows(a: pd.DataFrame, gap_s: float = WINDOW_GAP_S) -> pd.DataFrame:
    """Window index within each short capture: new window at the first attempt or when the foot lifts
    at least gap_s after the previous attempt ended. Long captures get window 1."""
    a = a.sort_values(["RADAR_capture", "an"]).copy()
    prev_end = a.groupby("RADAR_capture")["t_end"].shift()
    gap = a["t_foot_up"] - prev_end
    new = prev_end.isna() | (gap >= gap_s)
    a["window"] = new.groupby(a["RADAR_capture"]).cumsum().astype(int)
    a.loc[a["task"] == "long", "window"] = 1
    a["window_id"] = a["RADAR_capture"] + "_w" + a["window"].astype(str)
    rel = a["t_foot_up"] - a["MOCAP_Start_Time"]
    a["window_timeband"] = np.select([rel < 7.0, rel <= 14.5], [1, 2], 3)
    pos = a.groupby("window_id").cumcount()
    n_in = a.groupby("window_id")["an"].transform("size")
    a["first_in_window"] = pos == 0
    a["early_touchdown"] = (pos < n_in - 1) | a["never_stable"]
    return a


def window_table(a: pd.DataFrame) -> pd.DataFrame:
    s = a[a["task"] == "short"]
    g = s.groupby("window_id", sort=False)
    first = s[s["first_in_window"]].set_index("window_id")
    w = pd.DataFrame({
        "pid": g["pid"].first(), "age_group": g["age_group"].first(), "stance": g["stance"].first(),
        "version": g["version"].first(), "capture": g["RADAR_capture"].first(), "window": g["window"].first(),
        "n_attempts": g.size(), "any_never_stable": g["never_stable"].any(),
    })
    w["failure"] = (w["n_attempts"] >= 2) | w["any_never_stable"]
    w["first_tts"] = first["tts"]
    w["first_hold"] = first["hold"].where(~first["never_stable"], 0.0)
    w.loc[~first["order_ok"], "first_hold"] = np.nan
    w["first_censored"] = first["censored"]
    w["self_assessment"] = g["self_assessment"].first()
    return w.reset_index()
