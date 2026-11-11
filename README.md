# OLST Balance Lab

A transparent, reproducible re-analysis of one open PhysioNet deposit of one-leg stance recordings in 32
healthy adults: on the same short, cued one-leg yoga tree task, how do younger and older adults differ in how
often they need a retry, how fast they settle, and how long the first stable hold lasts?

**Status: public.** Code, documents, aggregate results and the two official metadata tables on GitHub
(https://github.com/victorgomezadapty/olst-balance-lab). Kaggle dataset (the two official metadata tables
only, with attribution): https://www.kaggle.com/datasets/vctorandrsgmezlpez/one-leg-stance-events-in-young-and-older-adults. Kaggle notebook (the metadata analysis, runs from those two tables):
https://www.kaggle.com/code/vctorandrsgmezlpez/olst-balance-lab-one-leg-stance-re-analysis. A portfolio case will follow; there is no dedicated
Vercel site. Raw force-plate, motion capture, QTM and radar signals stay local and gitignored (see
[DATA_LICENSE.md](DATA_LICENSE.md)).

## About the name

The deposit's official title is *Multimodal Synchronized Motion Capture, Force Plate, and Radar Dataset of
the One-Legged Stand Test for Fall-Risk Assessment* (PhysioNet, version 1.0, DOI 10.13026/46hn-6b25), by
Daniel Copeland, Evan Linton, Xiang Zhang, Hector Lugaro, Buntoku Mori and Brian Anthony. "OLST Balance Lab"
is only this project's short name (package `olst_balance_lab`).

## Read this first: the task is not the clinical one-leg stand test

Participants entered a yoga tree pose (sole of the lifted foot on the inner thigh or calf) with both arms
overhead, inside cued windows of about 4 s, and retried within the window if they touched down early. Older
adults also did 20 s windows; younger adults did not. The clinical one-leg stand or unipedal stance test is
usually timed with arms at the side or crossed, up to 10, 30 or 45 s. **None of the hold times here is a
clinical OLST time, and nothing here is a fall risk score or a clinical cut off.** The sample is healthy
volunteers only, aged 19 to 32 and 64 to 78, with no middle aged group.

## Main result (primary, pre-specified)

All short captures of all 32 people (15 Young, 17 Old), attempts grouped into cued windows by a written rule
(267 Young windows, 362 Old windows). One summary per person, then Old minus Young, 95% bootstrap CI with
persons resampled within group.

| Endpoint | Young | Old | Old minus Young |
|-|-|-|-|
| Windows not completed in one stable attempt | 1.9% (0.4% to 3.8%) | 28.0% (17.5% to 40.2%) | +26.0 points (+15.4 to +38.4) |
| Time to stability, s (first attempt per window, person median) | 0.59 (0.54 to 0.65) | 0.34 (0.28 to 0.40) | -0.25 (-0.33 to -0.17) |
| First attempt stable hold, s (person median, 0 if never stable) | 3.35 (3.28 to 3.43) | 2.52 (2.14 to 2.88) | -0.83 (-1.23 to -0.46) |

The plain reading: in this healthy sample, younger adults almost always completed a 4 s window in one stable
attempt; older adults needed a retry or never settled in about one window in four, with a wide spread between
people (interquartile range 11% to 29% of windows). Their first stable hold was about 0.8 s shorter. But the best hold any older adult produced
in a short window was as long as the younger adults' (sensitivity S4: +0.18 s, -0.18 to +0.54). On this task
the age difference is mainly about consistency, not about the longest hold someone can produce.

**A counterintuitive result, reported as found.** Older adults reached the labelled "start of stability"
sooner (0.34 vs 0.59 s). That label comes from the lifted knee angle settling, not from sway. The force-plate
check below shows the stance foot centre of pressure keeps settling for about 1.3 s after that label in both
groups, so a shorter time to stability here should not be read as faster balance recovery.

Sensitivities (person mean; all valid attempts clustered by person; censored windows removed; versions V1 to
V3 only) keep the direction and size of the failure and hold differences; the final attempt only and best
hold samples do not show a hold difference. Full numbers: [RESULTS.md](RESULTS.md) and `results/summary.json`.

## Force-plate check of the official labels

All 418 short capture force-plate CSVs (about 2.2 GB) were downloaded and verified against the official
checksums (one labelled capture has no force-plate file in the deposit). On 557 attempts with complete event
labels, the lifted foot plate was unloaded during every labelled stable phase (100%). Under the pre-specified
rule (stance COP speed lowest in the stable phase compared with both the foot up and foot down phases),
agreement was only 39% (31% to 47%): the foot down phase is often just as quiet. The stable phase was slower
than the foot up phase in 80% (post hoc, descriptive). A simple COP based stability onset fell a median 1.3 s
after `t_stable`, within 0.5 s in only 14%. The labels mark posture, not quiet sway.

## What this project adds

1. **Deposit audit.** Files checked against the project card and README; nothing silently corrected.
   Main flags: the README names `12_MNTRL_V2` as the missing capture, but the files hold V2 and V3 and lack
   V1; 43 extra V4 captures in the Old group (334 captures, not 294); 20 captures with no attempt flagged
   `is_attempt_final`; 237 attempts end at the recording end (censored); one capture without force-plate
   files; three radar frame indices that disagree with the time conversion; out of date citation line.
2. **A protocol translation for clinicians** and an explicit warning that a present `t_break` in a 4 s cued
   window is usually the end cue, not a loss of balance.
3. **A fair Young vs Old comparison** on the short task only, with window level outcomes that respect the
   retry design, person level summaries and person resampled CIs, and six sensitivities.
4. **An independent force-plate check** of the official MOCAP based stability labels.
5. Stance foot (left vs right) and self rated balance, labelled descriptive; long 20 s windows reported
   separately for the Old group only.

## What this project is not

* Not a second data descriptor and not a restatement of the companion paper (which describes the
  collection, the sensors, the event tagging pipeline, radar processing and technical validation). It is
  cited only; its text, tables, figures, code and coefficients are not reused, and the deposit `Figures/`
  folder was never downloaded.
* Not a radar or motion capture modelling study.
* Not fall risk diagnosis, not a clinical cut off, and not evidence that yoga tree hold times equal
  clinical OLST times.
* Not a data release. Outputs are aggregates.

## Discussion and open questions

See [DISCUSSION.md](DISCUSSION.md): limitations (task mismatch, healthy only sample, no middle aged group,
long windows only in the Old group, uneven attempt counts), a short literature note, and what remains to
investigate.

## Project layout

| Path | Content |
|-|-|
| `data/raw/Participant_Demographics.csv`, `data/raw/OLST_Attempts.csv` | Official metadata tables, unmodified, hash checked |
| `data/raw/LICENSE.txt`, `data/raw/SHA256SUMS.txt` | Unmodified deposit files |
| `data/raw/README.txt`, `data/raw/Raw/ForcePlate/` | Local only, gitignored |
| `src/olst_balance_lab/` | `data` (hashes), `events` (definitions, windows), `audit`, `analysis`, `stats`, `forceplate`, `figures`, `report` |
| `scripts/fetch_data.py` | Copies or downloads official files and stops on any sha256 mismatch, with `forceplate` it adds the short capture force-plate CSVs |
| `scripts/run_analysis.py` | Regenerates `tables/`, `figures/`, `results/summary.json`, `RESULTS.md` |
| `tests/` | Integrity, refusal on mismatch, definitions, sample, outputs, license, privacy and copy tests |
| `tables/` | 14 CSV tables, aggregates only; cells describing a single person are suppressed |
| `figures/` | 7 figures as PNG with WebP twins |
| `ANALYSIS_PLAN.md` | Pre-specified plan (committed before outcome results) |
| `PORTFOLIO_BRIEF.md` | Locked facts for a later portfolio case |

## Reproduce

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_data.py forceplate   # official files, sha256 verified; about 2.2 GB
.venv/bin/python scripts/run_analysis.py
.venv/bin/python -m pytest -q
```

Without `forceplate` the metadata analysis runs in full and the force-plate check is recorded as skipped.

## Citation and license

Data: Copeland, D., Linton, E., Zhang, X., Lugaro, H., Mori, B., and Anthony, B. (2026). Multimodal
Synchronized Motion Capture, Force Plate, and Radar Dataset of the One-Legged Stand Test for Fall-Risk
Assessment (version 1.0). PhysioNet. RRID:SCR_007345. https://doi.org/10.13026/46hn-6b25. License CC BY 4.0.
Also cite PhysioNet: Pollard et al. 2026, Nature Health, https://doi.org/10.1038/s44360-026-00096-z.

Companion paper (cited only, CC BY-NC-ND 4.0): Copeland D, Zhang X, Linton E, Mori B, Lugaro H, Anthony BW.
One-Legged Stand Test: Synchronized Motion Capture, Force Plate, and Radar Dataset for Fall-Risk. Scientific
Data, 2026. https://doi.org/10.1038/s41597-026-06831-1

The creators, PhysioNet and MIT do not endorse this project. Code: MIT ([LICENSE](LICENSE)), copyright 2026
Víctor Andrés Gómez López. Provenance: [PROVENANCE.md](PROVENANCE.md).
