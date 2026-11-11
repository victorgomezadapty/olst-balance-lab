# Data license and attribution

## Data source

The only data used in this project is the following PhysioNet deposit:

> Copeland, D., Linton, E., Zhang, X., Lugaro, H., Mori, B., and Anthony, B. (2026). Multimodal Synchronized
> Motion Capture, Force Plate, and Radar Dataset of the One-Legged Stand Test for Fall-Risk Assessment
> (version 1.0). PhysioNet. RRID:SCR_007345. https://doi.org/10.13026/46hn-6b25

* Creators, in the order of the project card: Daniel Copeland, Evan Linton, Xiang Zhang, Hector Lugaro,
  Buntoku Mori, Brian Anthony.
* Version DOI 10.13026/46hn-6b25; concept (latest version) DOI 10.13026/70xa-vm53; published 25 January
  2026; page https://physionet.org/content/olst-mocap-forceplate-radar/1.0/
* PhysioNet standard citation, as requested on the page: Pollard, T., et al. (2026). PhysioNet as a
  global platform for biomedical research. Nature Health. https://doi.org/10.1038/s44360-026-00096-z
* "OLST Balance Lab" is only this project's short name. It is not the deposit title.

## License

* Access: Open Access. No data use agreement, no credentialed access, no training requirement.
* License: **Creative Commons Attribution 4.0 International (CC BY 4.0)**,
  https://creativecommons.org/licenses/by/4.0/. The deposited `LICENSE.txt` (sha256
  `9a78e7f22742dde9f66ae235ec793ba2212019dc4d0ced75c4da09ced0b35fb2`, 14,842 bytes), the project card and the
  page metadata all state CC BY 4.0. There is no contradiction between them.
* CC BY 4.0 allows sharing and adapting the data, including redistribution of the official files, with
  attribution, a link to the license and an indication of changes.

## What this project keeps and what it does not

* Kept in the project tree, unmodified and hash checked on every load: `data/raw/Participant_Demographics.csv`
  (sha256 `92d8b45db27dd28af0949c735dc83027d4ec89ff76b21f3e7a403cd569cb83f5`, 984 bytes),
  `data/raw/OLST_Attempts.csv` (sha256 `fdfed70659a153f0be3a19edaf8c810ddb9d91c29f1668b8b95f80e192e3253b`,
  133,530 bytes, 1,241 attempt rows), `data/raw/LICENSE.txt` and `data/raw/SHA256SUMS.txt`.
* Kept local only and listed in `.gitignore`: the deposit `README.txt` (it is used for the audit; it carries a
  personal contact line that this project does not need to repeat) and any raw signal file: force plate
  CSVs under `data/raw/Raw/ForcePlate/`, and if ever downloaded, motion capture, QTM and radar files. As a
  practical rule, raw signals are never committed or placed in any folder meant for publication, even though
  the license would allow it. The full deposit is about 10 GB.
* Not downloaded or used: the deposit `Figures/` folder, the QTM project, the radar Range Doppler Maps and
  the motion capture tree.
* All outputs (`tables/`, `figures/`, `results/summary.json`, `RESULTS.md`) are aggregate research results:
  counts, means, medians, shares, intervals. Figure 3 shows one summary dot per person with no identifier.
  No individual trace is shown.
* The outputs are not offered as a separate data release under any new license. If shown, they carry the
  CC BY 4.0 attribution above.

### Changes made (CC BY 4.0 section 3(a)(1)(B))

* No change to any deposited file. Every file used is checked against the official `SHA256SUMS.txt`.
* In memory only: columns renamed; height converted from inches to cm and weight from pounds to kg; capture
  identifiers parsed into participant, movement code, stance foot and version; event intervals computed;
  attempts grouped into cued windows by a written rule; force plate COP smoothed and differentiated.
* Aggregation and statistical summaries only.

## Out of date statement in the deposit README

The deposit `README.txt` still cites the data descriptor as "Scientific Data, 2025. Under review." That line
is out of date: the paper was published on 25 February 2026 (below). The README also says the missing
capture is `12_MNTRL_V2`; in the files the absent capture for participant 12, left base short task, is V1
(see RESULTS.md, flag A4). Both are flagged, not corrected.

## Companion paper (cited only)

> Copeland D, Zhang X, Linton E, Mori B, Lugaro H, Anthony BW. One-Legged Stand Test: Synchronized Motion
> Capture, Force Plate, and Radar Dataset for Fall-Risk. Scientific Data. Published 25 Feb 2026.
> https://doi.org/10.1038/s41597-026-06831-1

The paper is licensed CC BY-NC-ND 4.0, which does not allow sharing adapted material. It was read only to
understand the protocol and to avoid repeating its content. No text, tables, figures, code or coefficients
from it are reused, and no figure of this project is derived from its figures.

## Endorsement and funding

The creators, PhysioNet and MIT do not endorse this project or its interpretation. The original study was
approved by the MIT Committee on the Use of Humans as Experimental Subjects (COUHES #1911000055), with
written consent and HIPAA Safe Harbor de-identification, and was funded by Sekisui House Ltd. This project
had no contact with the creators.

## Code

The code in `src/`, `scripts/` and `tests/` is licensed under the MIT License (see `LICENSE`), copyright
2026 Víctor Andrés Gómez López. The MIT license does not apply to the data, to the deposited files, or to
the derived results.
