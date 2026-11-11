# Pre-specified analysis plan

Written and saved on 11 Nov 2026 (UTC+3). Before writing it I had: verified the hashes of the
official files; read the deposit README and the protocol section of the companion data descriptor
(to understand the task, not to reuse anything); and run structural audit counts on
`OLST_Attempts.csv` (movement codes, captures per code and age group, attempts per capture, missing
event fields, gaps between consecutive attempts, capture end truncation). Attempts per capture by
age group were seen as part of that audit. No time to stability, hold duration or balance loss
summary by age group, stance foot or self assessment had been computed. Any later change is listed
at the end of this file with its reason.

## Question

In the open PhysioNet OLST deposit, how do healthy younger (32 or under) and older (64 and over)
adults differ on the same short one-leg yoga tree task, measured with the official event labels:
how quickly they reach a stable stance, how long the first stable hold lasts inside a cued 4 s
window, and how often a window is not completed in one stable attempt? Do the labels line up with a
simple force-plate feature?

## 0. Data and integrity

Only `Participant_Demographics.csv` and `OLST_Attempts.csv` (official, unmodified) for the main
analysis, both checked against the official `SHA256SUMS.txt` and pinned sizes on every load. Values
are never edited; renaming and unit conversion happen in memory only.

## 1. Deposit audit (flag, never correct)

Compare files with the project card and README: participant count and ID range (gaps expected),
Young and Old counts and ages, Age_Group against age, units (height in inches, weight in pounds; BMI
recomputed in metric units and compared), missing capture `12_MNTRL_V2`, captures per participant,
code and version (the protocol describes three captures per leg and task), attempts per capture,
`is_attempt_final` against the number of captures, `an` continuity, missing `t_stable` and
`t_break`, event ordering (`t_foot_up <= t_stable <= t_break <= t_end`), attempts ending at the
capture end (`t_end` equal to `MOCAP_End_Time`), frame and time consistency through
`Seconds_per_Frame`, and its variation. README statements that are out of date are flagged.

## 2. Protocol translation (reported prominently)

* Task: a yoga tree pose (sole of the lifted foot against the inner thigh or calf of the stance
  leg) with both arms held overhead, entered from two-leg standing. It is not the classic clinical
  one-leg stand or unipedal stance test (arms at the side or crossed, foot lifted freely, timed to
  a maximum such as 10, 30 or 45 s).
* Codes: `MNTRL` and `MNTRR` are short Mountain-to-Tree captures, three cued 4 s windows each, left
  (L) or right (R) foot as base. `TRLGL` and `TRLGR` are long captures with one 20 s window, Old only.
* Inside a window, a person who touched down early was asked to try again until the window closed.
* Consequences: in short windows the end of stability is usually the end cue, so a present
  `t_break` is not by itself a loss of balance; holds are capped near 4 s; people with poorer
  balance contribute more, shorter attempts. None of these hold times is a clinical OLST time.

## 3. Event definitions (per attempt)

* Time to stability (TTS) = `t_stable - t_foot_up`, only when `t_stable` is present.
* Stable hold = `t_break - t_stable` when `t_break` is present, else `t_end - t_stable`. When the
  hold ends at the capture end (`t_end` equal to `MOCAP_End_Time` within 0.005 s) it is flagged as
  right censored by the recording.
* Never stable: `t_stable` missing. TTS and hold are not invented; for the first attempt hold
  endpoint below a never stable first attempt counts as 0 s of stable hold.
* Attempts with events out of order are flagged and excluded from the timing endpoints (counted).
* Naive balance loss label (as listed in the brief): `t_break` present. Reported, but labelled as
  confounded by the end cue in short windows.

## 4. Window assignment (short captures)

Within each short capture, attempts are ordered by `an`. A new cue window starts at the first
attempt and whenever `t_foot_up` is at least 2.0 s after the previous attempt's `t_end`. Agreement
with a simple time band rule (foot lift less than 7 s, 7 to 14.5 s, more than 14.5 s after
`MOCAP_Start_Time`) is reported in the audit.

* Window not completed cleanly (window failure) = the window has two or more attempts, or any of
  its attempts never reached stability.
* Early touchdown (attempt level) = the attempt is followed by another attempt in the same window,
  or never reached stability.

## 5. Primary sample (fixed)

All short captures (`MNTRL`, `MNTRR`) of all 32 participants (both age groups did this task), all
windows, both stance feet pooled. The unit of inference is the participant: each endpoint is first
summarised per person, then compared between groups. Long captures are never in this sample.

## 6. Primary endpoints (Old minus Young)

1. Window failure share: per person, the share of short windows not completed cleanly.
2. TTS: per person, the median TTS of the first attempt of each window that reached stability.
3. First attempt stable hold: per person, the median stable hold of the first attempt of each
   window (0 s if never stable).

For each: group mean of the person summaries with a 95% percentile bootstrap CI (persons resampled
within group, 5000 resamples, seed 20261111); Old minus Young difference with the same bootstrap
CI and, as a check, a Welch t interval; group medians are also shown. Also reported, from the same
sample: naive `t_break` share and early touchdown share per person, attempts per window.

## 7. Sensitivities (same three endpoints where defined)

* S1 all valid short attempts, attempt level, uncertainty by person cluster bootstrap: TTS of all
  attempts that reached stability; hold of all attempts that reached stability; early touchdown
  share; naive `t_break` share.
* S2 person mean instead of person median.
* S3 final attempt only (`is_attempt_final` True), one per capture, then person median.
* S4 best hold: per person, the longest stable hold of any short attempt.
* S5 windows whose first attempt is censored by the capture end removed.
* S6 versions V1 to V3 only (the protocol describes three captures per leg; extra versions removed).

## 8. Secondary and descriptive

* Stance foot: per person, left base minus right base for the three endpoints; mean paired
  difference with a person bootstrap CI, all participants and by group.
* Balance Self Assessment (1 to 5) against window failure share and first attempt hold: Spearman
  correlation by group with a bootstrap CI, labelled descriptive (small groups, narrow scale).
* Long captures, Old only, separate section, never compared with Young: per capture the longest
  stable hold, total stable time, number of attempts and censoring; summarised per person. No
  threshold is offered as a cut off.

## 9. Optional force-plate check (independent of the timing endpoints)

Only if the `Raw/ForcePlate` CSVs (inventoried by HTTP size, about 3.5 GB) download and verify
against `SHA256SUMS.txt`. Files are named `ID_CODE_FP_Vn_left.csv` and `..._right.csv`; the stance
plate is the base foot named by the code. Rules, per short attempt with all four events:

* Unloading check: the lifted foot plate vertical force (`Force_Z`) median between `t_stable` and
  `t_break` is below 5% of the stance plate median in the same interval (the foot is truly off).
* Stance COP speed: COP X and Y of the stance plate smoothed with a centred 50 ms moving mean,
  speed from the gradient (mm/s), samples with stance `Force_Z` below 20 N removed. Median COP
  speed in the foot up phase (`t_foot_up` to `t_stable`), the labelled stable phase (`t_stable` to
  `t_break`) and the foot down phase (`t_break` to `t_end`). Agreement = stable phase median lower
  than both other phases.
* Force-plate stability onset: first time after `t_foot_up` at which the 250 ms rolling mean stance
  COP speed falls below the median of that rolling speed over `t_foot_up` to `t_end` and stays
  below it for 0.5 s. Difference from `t_stable` (median, IQR, share within 0.5 s), by group.

This is an internal consistency check of the labels, not a validation study. If the download fails
or is too slow, it is skipped and documented as future work.

## 10. Not done

No fall risk classification, no clinical cut off, no comparison with clinical OLST norms as if the
tasks were the same, no radar or motion capture modelling, no reuse of the companion paper's text,
tables, figures, code or coefficients.

## Changes after this plan was saved

None yet.
