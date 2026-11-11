"""Deposit audit (ANALYSIS_PLAN.md section 1). Everything is flagged; nothing is corrected."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data as D


def audit(demo_raw: pd.DataFrame, demo: pd.DataFrame, a: pd.DataFrame, raw_dir=D.RAW_DIR):
    f = {}
    f["n_participants"] = int(demo["pid"].nunique())
    f["n_young"] = int((demo["age_group"] == "Young").sum())
    f["n_old"] = int((demo["age_group"] == "Old").sum())
    f["id_min"], f["id_max"] = int(demo["pid"].min()), int(demo["pid"].max())
    f["ids_absent_in_range"] = int(f["id_max"] - f["id_min"] + 1 - f["n_participants"])
    f["age_range"] = [int(demo["age"].min()), int(demo["age"].max())]
    f["age_range_young"] = [int(demo.loc[demo.age_group == "Young", "age"].min()), int(demo.loc[demo.age_group == "Young", "age"].max())]
    f["age_range_old"] = [int(demo.loc[demo.age_group == "Old", "age"].min()), int(demo.loc[demo.age_group == "Old", "age"].max())]
    f["n_under_18"] = int((demo["age"] < 18).sum())
    f["n_aged_19_or_20"] = int(demo["age"].isin([19, 20]).sum())
    f["age_group_inconsistent"] = int((((demo["age_group"] == "Young") & (demo["age"] > 32)) |
                                       ((demo["age_group"] == "Old") & (demo["age"] < 64))).sum())
    f["gender_counts"] = {"1 (M)": int((demo["gender"] == 1).sum()), "2 (F)": int((demo["gender"] == 2).sum())}
    f["height_unit"], f["weight_unit"] = "inches", "pounds"
    f["bmi_max_abs_diff_recomputed"] = round(float((demo["bmi"] - demo["bmi_recomputed"]).abs().max()), 3)
    f["bmi_n_diff_over_0_1"] = int(((demo["bmi"] - demo["bmi_recomputed"]).abs() > 0.1).sum())
    f["self_assessment_values"] = sorted(int(x) for x in demo["self_assessment"].unique())
    f["demographics_has_bom"] = demo_raw.columns[0] == "Participant_ID"  # read with utf-8-sig; see below
    caps = a.groupby("RADAR_capture").agg(pid=("pid", "first"), code=("code", "first"), task=("task", "first"),
                                          version=("version", "first"), group=("age_group", "first"),
                                          n=("an", "size"), max_an=("an", "max"), finals=("is_attempt_final", "sum"),
                                          start=("MOCAP_Start_Time", "first"), end=("MOCAP_End_Time", "first"))
    f["n_attempts"] = int(len(a))
    f["n_captures"] = int(len(caps))
    f["modalities_in_attempts"] = sorted(a["modality"].unique().tolist())
    f["captures_by_code_group"] = {f"{k[0]}|{k[1]}": int(v) for k, v in caps.groupby(["code", "group"]).size().items()}
    f["attempts_by_code_group"] = {f"{k[0]}|{k[1]}": int(v) for k, v in a.groupby(["code", "age_group"]).size().items()}
    expected_caps = f["n_young"] * 6 + f["n_old"] * 12
    f["captures_expected_by_protocol"] = int(expected_caps)
    f["captures_beyond_v3"] = int((~caps["version"].isin(["V1", "V2", "V3"])).sum())
    f["captures_beyond_v3_by_group"] = {k: int(v) for k, v in caps[~caps["version"].isin(["V1", "V2", "V3"])].groupby("group").size().items()}
    have = set(caps.index)
    f["capture_12_MNTRL_V2_present"] = "12_MNTRL_RR_V2" in have
    f["participant_12_MNTRL_versions_in_attempts"] = sorted(c.split("_")[-1] for c in have if c.startswith("12_MNTRL_"))
    sums = D.parse_sums((raw_dir / D.SUMS_FILE).read_text(encoding="utf-8"))
    f["participant_12_MNTRL_versions_raw_forceplate"] = sorted({k.split("_")[3] for k in sums if k.startswith("Raw/ForcePlate/12/12_MNTRL_")})
    f["participant_12_MNTRL_versions_raw_mocap"] = sorted({k.split("_")[3] for k in sums if k.startswith("Raw/MOCAP/12/12_MNTRL_")})
    f["participant_12_MNTRL_versions_qtm"] = sorted({k.rsplit("/", 1)[1].split("_")[3].split(".")[0] for k in sums if k.startswith("OLST_QTM/Data/12/12_MNTRL_")})
    pc = caps.groupby(["pid", "code"]).size().unstack(fill_value=0)
    short_cells = pc[["MNTRL", "MNTRR"]].stack()
    f["person_code_cells_short_not_3"] = {f"{i}|{c}": int(v) for (i, c), v in short_cells[short_cells != 3].items()}
    f["an_gaps"] = int((caps["n"] != caps["max_an"]).sum())
    f["attempts_per_capture"] = {int(k): int(v) for k, v in caps["n"].value_counts().sort_index().items()}
    f["finals_true"] = int(a["is_attempt_final"].sum())
    f["captures_with_final_flag"] = int((caps["finals"] == 1).sum())
    f["captures_without_final_flag"] = int((caps["finals"] == 0).sum())
    nf = caps[caps["finals"] == 0]
    f["captures_without_final_by_code"] = {k: int(v) for k, v in nf["code"].value_counts().items()}
    f["captures_without_final_by_group"] = {k: int(v) for k, v in nf["group"].value_counts().items()}
    last = a.groupby("RADAR_capture")["an"].transform("max") == a["an"]
    f["final_flag_not_on_last_attempt"] = int((a["is_attempt_final"] & ~last).sum())
    f["missing_t_stable"] = int(a["t_stable"].isna().sum())
    f["missing_t_break"] = int(a["t_break"].isna().sum())
    f["missing_t_foot_up_or_t_end"] = int(a[["t_foot_up", "t_end"]].isna().any(axis=1).sum())
    f["break_without_stable"] = int((a["t_break"].notna() & a["t_stable"].isna()).sum())
    f["event_order_violations"] = int((~a["order_ok"]).sum())
    f["censored_at_capture_end"] = int(a["censored"].sum())
    f["censored_without_break"] = int((a["censored"] & a["t_break"].isna()).sum())
    f["censored_with_break"] = int((a["censored"] & a["t_break"].notna()).sum())
    f["no_break_not_censored"] = int((~a["censored"] & a["t_break"].isna()).sum())
    f["no_break_not_censored_but_stable"] = int((~a["censored"] & a["t_break"].isna() & a["t_stable"].notna()).sum())
    f["very_short_attempts_under_0_5s"] = int((a["attempt_len"] < 0.5).sum())
    win = caps["end"] - caps["start"]
    f["capture_sync_window_s"] = {"min": float(win.min()), "median": float(win.median()), "max": float(win.max())}
    f["captures_sync_window_under_15s"] = int((win < 15).sum())
    spf = a.groupby("RADAR_capture")["Seconds_per_Frame"].first()
    rec = (a["MOCAP_End_Time"] - a["MOCAP_Start_Time"]) / (a["RADAR_End_Frame"] - a["RADAR_Start_Frame"])
    f["seconds_per_frame_recompute_max_abs_diff"] = float((rec - a["Seconds_per_Frame"]).abs().max())
    f["seconds_per_frame"] = {"mean": float(spf.mean()), "sd": float(spf.std()), "min": float(spf.min()), "max": float(spf.max())}
    f["seconds_per_frame_within_person_sd_median"] = float(spf.groupby(caps["pid"]).std().median())
    pred = a["RADAR_Start_Frame"] + (a["t_foot_up"] - a["MOCAP_Start_Time"]) / a["Seconds_per_Frame"]
    f["frame_foot_up_vs_time_max_abs_frames"] = float((pred - a["frame_foot_up"]).abs().max())
    f["frame_foot_up_vs_time_over_2_frames"] = int(((pred - a["frame_foot_up"]).abs() > 2).sum())
    s = a[a["task"] == "short"]
    wpc = s.groupby("RADAR_capture")["window"].max()
    f["short_captures_windows"] = {int(k): int(v) for k, v in wpc.value_counts().sort_index().items()}
    f["window_rule_vs_timeband_agree"] = int((s["window"] == s["window_timeband"]).sum())
    f["window_rule_vs_timeband_n"] = int(len(s))
    short_caps = sorted(c for c in have if "_MNTR" in c or "_TRLG" in c)
    def _fp_keys(c):
        pid, code, _, ver = c.split("_")
        return [f"Raw/ForcePlate/{pid}/{pid}_{code}_FP_{ver}_{s}.csv" for s in ("left", "right")]
    def _mc_key(c):
        pid, code, _, ver = c.split("_")
        return f"Raw/MOCAP/{pid}/{pid}_{code}_MC_{ver}_pos.csv"
    f["captures_without_forceplate_in_deposit"] = [c for c in short_caps if not all(k in sums for k in _fp_keys(c))]
    f["captures_without_mocap_csv_in_deposit"] = [c for c in short_caps if _mc_key(c) not in sums]
    readme = (raw_dir / D.README_FILE).read_text(encoding="utf-8") if (raw_dir / D.README_FILE).exists() else ""
    f["readme_citation_says_under_review"] = "Under review" in readme
    f["readme_says_only_long_for_old"] = "Only long-duration (20 s) OLST trials are available for older adults" in readme

    flags = [
        ("A1", "info", "Participant IDs", f"{f['n_participants']} people, IDs {f['id_min']} to {f['id_max']} with {f['ids_absent_in_range']} absent numbers (screening IDs, per the descriptor); not 1 to 32"),
        ("A2", "info", "Units", "Height in inches and weight in pounds; converted in memory only. Stated BMI matches the metric recomputation within "
         f"{f['bmi_max_abs_diff_recomputed']} kg/m2"),
        ("A3", "ok" if f["age_group_inconsistent"] == 0 else "flag", "Age_Group vs age", f"{f['age_group_inconsistent']} inconsistent rows; Young {f['age_range_young'][0]} to {f['age_range_young'][1]}, Old {f['age_range_old'][0]} to {f['age_range_old'][1]}; no minors"),
        ("A4", "flag", "Missing capture label", "README and descriptor say 12_MNTRL_V2 is missing. The files hold 12_MNTRL versions "
         f"{', '.join(f['participant_12_MNTRL_versions_in_attempts'])} in OLST_Attempts.csv, {', '.join(f['participant_12_MNTRL_versions_raw_forceplate'])} in Raw/ForcePlate and "
         f"{', '.join(f['participant_12_MNTRL_versions_raw_mocap'])} in Raw/MOCAP (QTM folder: {', '.join(f['participant_12_MNTRL_versions_qtm'])}). The capture missing from the "
         "analysable files is V1, not V2; not corrected, only flagged"),
        ("A5", "flag", "Captures per protocol", f"{f['n_captures']} captures vs {expected_caps} implied by three captures per leg and task; {f['captures_beyond_v3']} captures are a fourth version (V4), all in the Old group"),
        ("A6", "flag", "is_attempt_final", f"{f['finals_true']} True for {f['n_captures']} captures: always on the last attempt, but {f['captures_without_final_flag']} captures (all Old, mostly long) have no final attempt flagged"),
        ("A7", "info", "Event completeness", f"t_stable missing in {f['missing_t_stable']} attempts (never stable), t_break missing in {f['missing_t_break']}; t_break never present without t_stable; {f['event_order_violations']} order violations"),
        ("A8", "flag", "Capture end truncation", f"{f['censored_at_capture_end']} attempts end exactly at MOCAP_End_Time (recording ended, not a touchdown); holds there are right censored"),
        ("A9", "flag", "t_break meaning in short windows", "In 4 s cued windows the end of stability is usually the end cue, so a present t_break is not by itself a loss of balance"),
        ("A10", "info", "Seconds_per_Frame", f"varies from {f['seconds_per_frame']['min']:.5f} to {f['seconds_per_frame']['max']:.5f} s across captures (SD {f['seconds_per_frame']['sd']:.5f}); recomputed from times and frames within {f['seconds_per_frame_recompute_max_abs_diff']:.1e} s"),
        ("A10b", "flag", "Frame vs time", f"{f['frame_foot_up_vs_time_over_2_frames']} attempts (one capture) have frame_foot_up more than 2 frames away from the time based conversion (max {f['frame_foot_up_vs_time_max_abs_frames']:.1f} frames); radar only, not used here"),
        ("A10c", "flag", "Force-plate files", f"labelled captures without force-plate CSVs in the deposit: {', '.join(f['captures_without_forceplate_in_deposit']) or 'none'}; without a MOCAP CSV: {', '.join(f['captures_without_mocap_csv_in_deposit']) or 'none'}"),
        ("A11", "flag", "Short sync window", f"{f['captures_sync_window_under_15s']} captures with a sync window under 15 s (min {f['capture_sync_window_s']['min']:.2f} s; median {f['capture_sync_window_s']['median']:.2f} s)"),
        ("A12", "info", "Window assignment", f"gap rule gives 3 windows in {f['short_captures_windows'].get(3, 0)} short captures and 2 in {f['short_captures_windows'].get(2, 0)}; agrees with the time band rule for {f['window_rule_vs_timeband_agree']} of {f['window_rule_vs_timeband_n']} short attempts"),
        ("A13", "flag", "README citation", "README still cites the descriptor as Scientific Data 2025, under review; it was published 25 Feb 2026 (DOI 10.1038/s41597-026-06831-1)"),
        ("A14", "flag", "README wording", "README says only long 20 s trials are available for older adults; the files show Old participants have both short and long captures, and long ones only exist for Old"),
    ]
    flags_df = pd.DataFrame(flags, columns=["flag", "severity", "item", "finding"])
    cmp_rows = [
        ("Participants", "32 (15 Young, 17 Old)", f"{f['n_participants']} ({f['n_young']} Young, {f['n_old']} Old)"),
        ("Age ranges", "Young 18 to 32, Old 64 and over", f"Young {f['age_range_young'][0]} to {f['age_range_young'][1]}, Old {f['age_range_old'][0]} to {f['age_range_old'][1]}"),
        ("Short captures per leg", "3 per person", f"{len(f['person_code_cells_short_not_3'])} person and leg cells not equal to 3"),
        ("Long captures", "Old only, 3 per leg", f"{f['captures_by_code_group'].get('TRLGL|Old', 0) + f['captures_by_code_group'].get('TRLGR|Old', 0)} captures, Old only"),
        ("Total captures", f"{expected_caps} implied", f"{f['n_captures']}"),
        ("Labelled attempts", "1,241", f"{f['n_attempts']:,}"),
        ("Missing capture", "12_MNTRL_V2", "V2 present; V1 absent from metadata and Raw"),
        ("Final attempt flag", "final window in the capture", f"{f['captures_with_final_flag']} of {f['n_captures']} captures flagged"),
    ]
    cmp_df = pd.DataFrame(cmp_rows, columns=["item", "card_or_readme", "files"])
    cmp_df["match"] = ["yes", "yes", "no" if f["person_code_cells_short_not_3"] else "yes", "partly", "no", "yes", "no", "partly"]
    return cmp_df, flags_df, f


def completeness_table(a: pd.DataFrame) -> pd.DataFrame:
    a = a.assign(event_set=np.select(
        [a["never_stable"], a["t_break"].notna(), a["censored"]],
        ["never stable (no t_stable)", "complete (t_stable and t_break)", "stable, no t_break, ended at capture end"],
        "stable, no t_break, ended before capture end"))
    t = a.groupby(["task", "age_group", "event_set"]).size().rename("attempts").reset_index()
    return t
