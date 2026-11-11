"""Figures (PNG with WebP twins). Original drawings from the official CSVs; nothing from the descriptor."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

FOOTER = ("Data: Copeland et al., PhysioNet olst-mocap-forceplate-radar 1.0, doi 10.13026/46hn-6b25, CC BY 4.0. "
          "Analysis: OLST Balance Lab. Yoga tree task, healthy adults only; not a clinical OLST time or fall risk test.")
COL = {"Young": "#3b75af", "Old": "#c8553d"}
TITLES = {
    "fig01": "Deposit audit: captures and event completeness",
    "fig02": "How the short and long captures are organised",
    "fig03": "Primary result: same 4 s task, Young vs Old (person level)",
    "fig04": "Sensitivity analyses: Old minus Young",
    "fig05": "Stance foot and self rated balance (descriptive)",
    "fig06": "Long 20 s captures, Old group only (descriptive)",
    "fig07": "Force-plate check of the official labels",
}
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def _save(fig, path: Path, caption: str) -> list[Path]:
    fig.text(0.01, 0.01, caption + "\n" + FOOTER, fontsize=7.3, color="#444", va="bottom", wrap=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    webp = path.with_suffix(".webp")
    Image.open(path).save(webp, "WEBP", quality=90, method=6)
    return [path, webp]


def fig_audit(facts: dict, completeness: pd.DataFrame, path: Path):
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.4))
    fig.subplots_adjust(bottom=0.27, top=0.85, wspace=0.35)
    fig.suptitle(TITLES["fig01"], x=0.01, ha="left", fontsize=12)
    ax = axs[0]
    cg = facts["captures_by_code_group"]
    codes = ["MNTRL", "MNTRR", "TRLGL", "TRLGR"]
    x = np.arange(len(codes))
    for i, g in enumerate(["Young", "Old"]):
        v = [cg.get(f"{c}|{g}", 0) for c in codes]
        ax.bar(x + (i - 0.5) * 0.38, v, 0.38, color=COL[g], label=g)
        for xi, vi in zip(x, v):
            ax.text(xi + (i - 0.5) * 0.38, vi + 1, str(vi), ha="center", fontsize=8)
    ax.axhline(45, color="#888", ls=":", lw=1)
    ax.axhline(51, color="#888", ls=":", lw=1)
    ax.text(1.65, 42.5, "3 per person: Young 45", fontsize=7, ha="center", color="#555")
    ax.text(1.65, 52.5, "3 per person: Old 51", fontsize=7, ha="center", color="#555")
    ax.set_xticks(x, ["short, left base", "short, right base", "long, left base", "long, right base"], fontsize=8)
    ax.set_ylabel("captures")
    ax.set_title(f"{facts['n_captures']} captures; {facts['captures_beyond_v3']} extra V4 captures (Old)", loc="left", fontsize=9.5)
    ax.legend(frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=2)
    ax = axs[1]
    order = ["complete (t_stable and t_break)", "stable, no t_break, ended at capture end",
             "stable, no t_break, ended before capture end", "never stable (no t_stable)"]
    cols = ["#4d8f4d", "#b8b8b8", "#e0c060", "#c0504d"]
    rows = [("short", "Young"), ("short", "Old"), ("long", "Old")]
    for j, (task, g) in enumerate(rows):
        d = completeness[(completeness.task == task) & (completeness.age_group == g)].set_index("event_set")["attempts"]
        tot = d.sum()
        left = 0
        for k, c in zip(order, cols):
            v = d.get(k, 0) / tot * 100
            ax.barh(j, v, left=left, color=c, label=k if j == 0 else None)
            if v > 6:
                ax.text(left + v / 2, j, f"{v:.0f}%", ha="center", va="center", fontsize=8, color="white")
            left += v
        ax.text(101, j, f"n={tot}", va="center", fontsize=8)
    ax.set_yticks(range(3), ["short, Young", "short, Old", "long, Old"])
    ax.set_xlim(0, 112)
    ax.set_xlabel("% of labelled attempts")
    ax.set_title("Event sets per attempt (nothing imputed)", loc="left", fontsize=9.5)
    ax.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.45, -0.14), ncol=2)
    return _save(fig, path, "Counts from OLST_Attempts.csv. Flags in tables/t02_audit_flags.csv.")


def fig_schematic(path: Path):
    fig, axs = plt.subplots(2, 1, figsize=(12, 5.2), gridspec_kw={"height_ratios": [1.3, 1]})
    fig.subplots_adjust(bottom=0.2, top=0.86, hspace=0.6)
    fig.suptitle(TITLES["fig02"], x=0.01, ha="left", fontsize=12)
    ax = axs[0]
    for k, w0 in enumerate([2.5, 10.2, 17.9]):
        ax.add_patch(plt.Rectangle((w0, 0.15), 4, 0.7, color="#e6eef7"))
        ax.text(w0 + 2, 0.92, f"cued window {k + 1} (about 4 s)", ha="center", fontsize=8)
    # window 1: clean; window 2: early touchdown and retry
    def att(ax, t0, ts, tb, te, y=0.5):
        ax.plot([t0, ts], [y, y], color="#e0a030", lw=6, solid_capstyle="butt")
        if tb is not None:
            ax.plot([ts, tb], [y, y], color="#4d8f4d", lw=6, solid_capstyle="butt")
            ax.plot([tb, te], [y, y], color="#999", lw=6, solid_capstyle="butt")
        else:
            ax.plot([ts, te], [y, y], color="#4d8f4d", lw=6, solid_capstyle="butt")
    att(ax, 2.8, 3.4, 6.3, 6.9)
    att(ax, 10.4, 10.9, 11.6, 12.0)
    att(ax, 12.4, 12.9, 13.9, 14.3)
    ax.plot([12.2, 12.5], [0.5, 0.5], color="#c0504d", lw=6)
    att(ax, 18.1, 18.6, None, 21.0)
    ax.axvline(21.0, color="#555", lw=1, ls=(0, (4, 2)))
    ax.text(21.1, 0.3, "capture ends:\nhold censored", fontsize=7.5)
    ax.text(4.6, 0.05, "clean window", ha="center", fontsize=7.5)
    ax.text(12.3, 0.05, "early touchdown, then retry = window failure", ha="center", fontsize=7.5)
    ax.set_xlim(0, 24); ax.set_ylim(0, 1.1); ax.set_yticks([]); ax.set_xlabel("time in capture, s (illustrative)")
    ax.set_title("Short capture (MNTRL, MNTRR): Young and Old", loc="left", fontsize=9.5)
    ax = axs[1]
    ax.add_patch(plt.Rectangle((2.5, 0.15), 20, 0.7, color="#f7ebe6"))
    ax.text(12.5, 0.92, "one cued window (about 20 s)", ha="center", fontsize=8)
    att(ax, 2.8, 3.5, 9.0, 9.6)
    att(ax, 10.6, 11.2, None, 22.4)
    ax.set_xlim(0, 24); ax.set_ylim(0, 1.1); ax.set_yticks([]); ax.set_xlabel("time in capture, s (illustrative)")
    ax.set_title("Long capture (TRLGL, TRLGR): Old only", loc="left", fontsize=9.5)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=c, lw=6) for c in ["#e0a030", "#4d8f4d", "#999"]]
    fig.legend(h, ["foot up phase: time to stability", "stable hold", "foot down phase"], frameon=False, fontsize=7.5,
               loc="upper right", bbox_to_anchor=(0.99, 0.99), ncol=3)
    return _save(fig, path, "Schematic drawn for this project from the event definitions; timings are illustrative, not data.")


def fig_primary(person: pd.DataFrame, prim: pd.DataFrame, path: Path):
    from .analysis import ENDPOINTS
    fig, axs = plt.subplots(1, 3, figsize=(12, 5))
    fig.subplots_adjust(bottom=0.25, top=0.8, wspace=0.4)
    fig.suptitle(TITLES["fig03"], x=0.01, ha="left", fontsize=12)
    rng = np.random.default_rng(1)
    short_t = {"window_failure_share": "Windows not completed in one stable attempt", "tts_s": "Time to stability (first attempt)",
               "first_hold_s": "First attempt stable hold (0 if never stable)"}
    for ax, (col, lab) in zip(axs, ENDPOINTS.items()):
        lab = short_t[col]
        r = prim.set_index("endpoint").loc[col]
        scale = 100 if col == "window_failure_share" else 1
        for i, g in enumerate(["Young", "Old"]):
            v = person.loc[person.age_group == g, col].dropna().to_numpy() * scale
            ax.scatter(i + rng.uniform(-0.12, 0.12, v.size), v, s=18, color=COL[g], alpha=0.55, lw=0)
            m, lo, hi = (r[f"{g.lower()}_mean"] * scale, r[f"{g.lower()}_ci95_low"] * scale, r[f"{g.lower()}_ci95_high"] * scale)
            ax.errorbar(i + 0.28, m, yerr=[[m - lo], [hi - m]], fmt="o", color="black", capsize=4, ms=5)
        ax.set_xticks([0, 1], [f"Young\nn={int(r.n_young)}", f"Old\nn={int(r.n_old)}"])
        ax.set_xlim(-0.5, 1.6)
        unit = "%" if scale == 100 else "s"
        d, dl, dh = r.diff_old_minus_young * scale, r.diff_ci95_low * scale, r.diff_ci95_high * scale
        ax.set_title(f"{lab}\nOld minus Young {d:+.2f} {unit} ({dl:+.2f} to {dh:+.2f})" if scale == 1 else
                     f"{lab}\nOld minus Young {d:+.1f} points ({dl:+.1f} to {dh:+.1f})", fontsize=8.5, loc="left")
        ax.set_ylabel("% of windows" if scale == 100 else "seconds")
    return _save(fig, path, "Dots: one summary per person (median over that person's short windows; failure as a share). "
                 "Black: group mean with 95% bootstrap CI (persons resampled). All short captures of all 32 people.")


def fig_sensitivity(prim: pd.DataFrame, sens: pd.DataFrame, s1: pd.DataFrame, path: Path):
    from .analysis import ENDPOINTS
    fig, axs = plt.subplots(1, 3, figsize=(12, 5.6))
    fig.subplots_adjust(left=0.24, bottom=0.2, top=0.85, wspace=0.15)
    fig.suptitle(TITLES["fig04"], x=0.01, ha="left", fontsize=12)
    s1m = s1.replace({"endpoint": {"early_touchdown_share": "window_failure_share", "hold_s_all_stable_attempts": "first_hold_s"}})
    allr = pd.concat([prim, sens, s1m[s1m.endpoint.isin(ENDPOINTS)]], ignore_index=True)
    labels = list(dict.fromkeys(allr["sample"]))
    names = {"primary": "Primary", "S1": "S1 all short attempts", "S2": "S2 person mean", "S3": "S3 final attempt only",
             "S4": "S4 best hold", "S5": "S5 censored windows removed", "S6": "S6 versions V1 to V3"}
    short = {l: names.get(l.split(" ")[0], l[:30]) for l in labels}
    heads = {"window_failure_share": "Window failure share", "tts_s": "Time to stability, s", "first_hold_s": "Stable hold, s"}
    for ax, col in zip(axs, ENDPOINTS):
        d = allr[allr.endpoint == col]
        if col == "window_failure_share":
            d = d[~d["sample"].str.startswith("S3")]  # degenerate: no final attempt is never stable
        for _, r in d.iterrows():
            y = labels.index(r["sample"])
            ax.errorbar(r.diff_old_minus_young, y, xerr=[[r.diff_old_minus_young - r.diff_ci95_low], [r.diff_ci95_high - r.diff_old_minus_young]],
                        fmt="o", color="black" if r["sample"] == "primary" else "#666", capsize=3)
        ax.axvline(0, color="#999", lw=1)
        ax.set_yticks(range(len(labels)), [short[l] for l in labels] if col == "window_failure_share" else [])
        ax.invert_yaxis()
        ax.set_title(heads[col], fontsize=9, loc="left")
    return _save(fig, path, "Old minus Young with 95% CI. S1 is attempt level (early touchdown share; hold of all stable attempts). "
                 "S3 is omitted for failure because no final attempt was ever unstable. Definitions in ANALYSIS_PLAN.md.")


def fig_stance_self(stance: pd.DataFrame, cells: pd.DataFrame, path: Path):
    fig = plt.figure(figsize=(13, 5))
    fig.suptitle(TITLES["fig05"], x=0.01, ha="left", fontsize=12)
    heads = {"window_failure_share": ("Window failure, points", 100), "tts_s": ("Time to stability, s", 1), "first_hold_s": ("Stable hold, s", 1)}
    groups = ["All", "Young", "Old"]
    for k, (col, (head, scale)) in enumerate(heads.items()):
        ax = fig.add_axes([0.06 + k * 0.17, 0.25, 0.13, 0.55])
        d = stance[stance.endpoint == col].set_index("group").loc[groups]
        for i, g in enumerate(groups):
            r = d.loc[g]
            m = r.mean_diff_left_minus_right * scale
            ax.errorbar(m, i, xerr=[[m - r.ci95_low * scale], [r.ci95_high * scale - m]], fmt="o", color=COL.get(g, "black"), capsize=3)
        ax.axvline(0, color="#999", lw=1)
        ax.set_yticks(range(3), groups if k == 0 else [])
        ax.invert_yaxis()
        ax.set_title(head, fontsize=9, loc="left")
    fig.text(0.06, 0.86, "Left base minus right base, paired within person (95% CI)", fontsize=9)
    ax = fig.add_axes([0.63, 0.25, 0.34, 0.55])
    for g in ["Young", "Old"]:
        c = cells[(cells.age_group == g) & ~cells.suppressed]
        off = 0.08 if g == "Old" else -0.08
        ax.scatter(c.self_assessment + off, c.mean_failure_share * 100, s=c.n_people * 25, color=COL[g], alpha=0.7, label=g)
        for _, r in c.iterrows():
            ax.text(r.self_assessment + off, r.mean_failure_share * 100 + 4, f"n={int(r.n_people)}", ha="center", fontsize=7)
    ax.set_xticks([1, 2, 3, 4, 5]); ax.set_xlim(0.5, 5.5); ax.set_ylim(-5, 100)
    ax.set_xlabel("Balance Self Assessment (as coded in the deposit)")
    ax.set_ylabel("mean window failure share, %")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Self rating vs observed short window failure", fontsize=9, loc="left")
    return _save(fig, path, "Descriptive only. Cells with a single person are suppressed (one Old cell, rating 2). Leg dominance was not recorded, so left vs right is not dominant vs non dominant.")


def fig_long(cap: pd.DataFrame, path: Path):
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
    fig.subplots_adjust(bottom=0.25, top=0.82, wspace=0.3)
    fig.suptitle(TITLES["fig06"], x=0.01, ha="left", fontsize=12)
    ax = axs[0]
    bins = np.arange(0, 23, 1)
    ax.hist([cap.loc[~cap.longest_is_censored, "longest_hold_s"], cap.loc[cap.longest_is_censored, "longest_hold_s"]], bins=bins,
            stacked=True, color=["#c8553d", "#e8b0a0"], label=["ended by touchdown or cue", "still holding when capture ended"])
    ax.set_xlabel("longest stable hold in the capture, s")
    ax.set_ylabel("captures")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title(f"{len(cap)} long captures, {cap.pid.nunique()} people", fontsize=9, loc="left")
    ax = axs[1]
    vc = cap["n_attempts"].clip(upper=8).value_counts().sort_index()
    ax.bar([str(i) if i < 8 else "8+" for i in vc.index], vc.values, color="#c8553d")
    ax.set_xlabel("attempts inside the 20 s window")
    ax.set_ylabel("captures")
    ax.set_title("Retries within one long window", fontsize=9, loc="left")
    return _save(fig, path, "Old only by design; there is no Young comparison for long windows. Not comparable to clinical one-leg stance norms.")


def fig_forceplate(fps: pd.DataFrame, path: Path):
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
    fig.subplots_adjust(bottom=0.27, top=0.82, wspace=0.45, left=0.25)
    fig.suptitle(TITLES["fig07"], x=0.01, ha="left", fontsize=12)
    ax = axs[0]
    d = fps[fps.check.str.contains("unloaded|lowest|within|lower than foot up")].reset_index(drop=True)
    for i, r in d.iterrows():
        ax.errorbar(r.share * 100, i, xerr=[[(r.share - r.ci95_low) * 100], [(r.ci95_high - r.share) * 100]], fmt="o",
                    color=COL.get(r.group, "black"), capsize=3)
    nick = {"lifted plate unloaded during labelled stable phase": "lifted foot unloaded in stable phase",
            "stance COP speed lowest in labelled stable phase": "COP slowest in stable phase (rule)",
            "stance COP speed lower than foot up phase (added after plan)": "COP slower than foot up (post hoc)",
            "force-plate onset within 0.5 s of t_stable": "COP onset within 0.5 s of t_stable"}
    ax.set_yticks(range(len(d)), [f"{r.group}: {nick.get(r.check, r.check)}" for _, r in d.iterrows()], fontsize=7.5)
    ax.set_xlim(0, 105)
    ax.invert_yaxis()
    ax.set_xlabel("% of attempts agreeing (95% person cluster CI)")
    ax = axs[1]
    m = fps[fps.check.str.startswith("median stance COP speed")]
    for gi, g in enumerate(["Young", "Old"]):
        mg = m[m.group == g]
        ph = [c.split(", ")[1].split(" ")[0] for c in mg.check]
        ax.bar(np.arange(len(ph)) + (gi - 0.5) * 0.38, mg.share, 0.38, color=COL[g], label=g)
        ax.set_xticks(np.arange(len(ph)), ["foot up", "stable", "foot down"][:len(ph)])
    ax.set_ylabel("median stance COP speed, mm/s")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Stance plate COP speed by labelled phase", fontsize=9, loc="left")
    return _save(fig, path, "Short attempts with force-plate files verified against SHA256SUMS.txt. Rules fixed in ANALYSIS_PLAN.md section 9.")
