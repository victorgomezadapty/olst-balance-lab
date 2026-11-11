"""Bootstrap and interval helpers. Persons are always the resampling unit."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as st

SEED = 20261111
N_BOOT = 5000


def pct_ci(x, alpha=0.05):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    return float(np.quantile(x, alpha / 2)), float(np.quantile(x, 1 - alpha / 2))


def boot_group_means(person: pd.DataFrame, col: str, group="age_group", a="Young", b="Old", n=N_BOOT, seed=SEED, stat=np.mean):
    """Group statistic of person level values and b minus a difference, persons resampled within group."""
    rng = np.random.default_rng(seed)
    xa = person.loc[person[group] == a, col].dropna().to_numpy(float)
    xb = person.loc[person[group] == b, col].dropna().to_numpy(float)
    ba = np.array([stat(rng.choice(xa, xa.size)) for _ in range(n)])
    bb = np.array([stat(rng.choice(xb, xb.size)) for _ in range(n)])
    w = st.ttest_ind(xb, xa, equal_var=False)
    wci = w.confidence_interval(0.95)
    return {
        "n_a": int(xa.size), "n_b": int(xb.size),
        "mean_a": float(stat(xa)), "ci_a": pct_ci(ba), "median_a": float(np.median(xa)),
        "mean_b": float(stat(xb)), "ci_b": pct_ci(bb), "median_b": float(np.median(xb)),
        "diff": float(stat(xb) - stat(xa)), "diff_ci": pct_ci(bb - ba),
        "welch_ci": (float(wci.low), float(wci.high)), "welch_p": float(w.pvalue),
    }


def boot_cluster_attempts(df: pd.DataFrame, col: str, group="age_group", a="Young", b="Old", n=N_BOOT, seed=SEED):
    """Attempt level mean per group with persons (pid) resampled within group, all their rows kept."""
    rng = np.random.default_rng(seed)
    out = {}
    res = {}
    for lab in (a, b):
        d = df[(df[group] == lab) & df[col].notna()]
        sums = d.groupby("pid")[col].sum()
        cnts = d.groupby("pid")[col].size()
        ids = sums.index.to_numpy()
        s, c = sums.to_numpy(float), cnts.to_numpy(float)
        bs = np.empty(n)
        for i in range(n):
            k = rng.integers(0, ids.size, ids.size)
            bs[i] = s[k].sum() / c[k].sum()
        res[lab] = bs
        out[lab] = {"n_rows": int(c.sum()), "n_people": int(ids.size), "mean": float(s.sum() / c.sum()), "ci": pct_ci(bs)}
    return {"n_a": out[a]["n_rows"], "people_a": out[a]["n_people"], "mean_a": out[a]["mean"], "ci_a": out[a]["ci"],
            "n_b": out[b]["n_rows"], "people_b": out[b]["n_people"], "mean_b": out[b]["mean"], "ci_b": out[b]["ci"],
            "diff": out[b]["mean"] - out[a]["mean"], "diff_ci": pct_ci(res[b] - res[a])}


def boot_paired_mean(d: np.ndarray, n=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    bs = np.array([rng.choice(d, d.size).mean() for _ in range(n)])
    return {"n": int(d.size), "mean": float(d.mean()), "ci": pct_ci(bs)}


def boot_spearman(x, y, n=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = ~np.isnan(x) & ~np.isnan(y)
    x, y = x[m], y[m]
    rho = st.spearmanr(x, y).statistic
    bs = []
    for _ in range(n):
        k = rng.integers(0, x.size, x.size)
        if np.unique(x[k]).size > 1 and np.unique(y[k]).size > 1:
            bs.append(st.spearmanr(x[k], y[k]).statistic)
    return {"n": int(x.size), "rho": float(rho), "ci": pct_ci(bs)}
