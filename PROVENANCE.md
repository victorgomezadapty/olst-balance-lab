# Data provenance

| Field | Value |
|-|-|
| Source | PhysioNet project `olst-mocap-forceplate-radar`, version 1.0 |
| Page | https://physionet.org/content/olst-mocap-forceplate-radar/1.0/ |
| Official title | Multimodal Synchronized Motion Capture, Force Plate, and Radar Dataset of the One-Legged Stand Test for Fall-Risk Assessment |
| Short name | "OLST Balance Lab" is only this project's short name (package `olst_balance_lab`); it is not the deposit title |
| Creators | Daniel Copeland, Evan Linton, Xiang Zhang, Hector Lugaro, Buntoku Mori, Brian Anthony |
| Version DOI | 10.13026/46hn-6b25 |
| Concept DOI | 10.13026/70xa-vm53 |
| Published | 25 January 2026 |
| Access | Open access, anyone can download; no data use agreement |
| License | CC BY 4.0 (`LICENSE.txt`, project card and metadata agree) |
| Content | 32 healthy adults (15 aged 19 to 32, 17 aged 64 to 78), 334 labelled captures, 1,241 labelled one-leg attempts; MOCAP 100 Hz, dual force plates 1200 Hz, 24 GHz FMCW radar |
| Ethics | MIT COUHES #1911000055, written consent, HIPAA Safe Harbor de-identification; funded by Sekisui House Ltd. |
| Identifiers | Study participant numbers (screening IDs 1 to 56 with gaps); no names or dates. Not shown in outputs |

## Files used and official checksums

| File (deposit path) | Bytes | sha256 | In git |
|-|-|-|-|
| `LICENSE.txt` | 14842 | `9a78e7f22742dde9f66ae235ec793ba2212019dc4d0ced75c4da09ced0b35fb2` | yes, unmodified |
| `SHA256SUMS.txt` | 178551 | `ac177ee0c4771088d722d0ff03df5a9bcc0968d2546089d587d07e4750e00da8` (measured on the plain file) | yes, unmodified |
| `Metadata/Participant_Demographics.csv` | 984 | `92d8b45db27dd28af0949c735dc83027d4ec89ff76b21f3e7a403cd569cb83f5` | yes, unmodified |
| `Metadata/OLST_Attempts.csv` | 133530 | `fdfed70659a153f0be3a19edaf8c810ddb9d91c29f1668b8b95f80e192e3253b` | yes, unmodified |
| `README.txt` | | `92f9d309d028b987f6f4fced8d89b24cf22ccedadc00ef29abe9d28f82a2d9db` | no, local only |
| `Raw/ForcePlate/*/*_MNTR?_FP_V?_{left,right}.csv` (418 files, about 2.2 GB) | | each checked against `SHA256SUMS.txt` | no, local only |

The metadata tables sit in `data/raw/` under their official names. `SHA256SUMS.txt` is the plain file; the
PhysioNet HTML viewer page for it is a different file and is never used.

## How the local copy was made

On 11 Nov 2026 (UTC+3):

1. `Participant_Demographics.csv` and `OLST_Attempts.csv` were copied (not moved) from an earlier verified
   local download whose sha256 matched the official values. Two HTML pages saved during an earlier failed
   attempt (404 shells) were ignored; the tests show such a file would be refused.
2. `LICENSE.txt` was copied from an earlier plain download (`/files/.../LICENSE.txt`, not the HTML viewer)
   and `SHA256SUMS.txt` from an earlier plain download; both were re-checked against the live PhysioNet files
   (identical sha256).
3. `README.txt` was downloaded from `https://physionet.org/files/olst-mocap-forceplate-radar/1.0/` and
   checked against `SHA256SUMS.txt`.
4. Force-plate sizes were inventoried by HTTP HEAD (668 files, 3.53 GB in total: 418 short capture files,
   2.23 GB; 250 long capture files, 1.30 GB). `scripts/fetch_data.py forceplate` then downloaded the 418
   short capture files to `.part` files, verified each sha256, and renamed them. Ten long capture files
   fetched before the download was narrowed remain local and unused.

Nothing was downloaded from `OLST_QTM/`, `Processed/Radar_RDMs/`, `Raw/MOCAP/` or `Figures/`.

## Rules for this project

1. This PhysioNet deposit is the only data source.
2. Size and sha256 of every official file used are checked on every load; the analysis stops on mismatch.
3. Outputs are aggregates. No attempt identifiers, no individual traces.
4. The companion paper is cited only. Its text, tables, figures, code and coefficients are not reused.
5. Public surfaces: the GitHub repository (code, documents, aggregate results, the two official metadata tables,
   `LICENSE.txt` and `SHA256SUMS.txt`) and a Kaggle dataset with the two official metadata tables only, plus a
   notebook. No dedicated Vercel site. Raw signals are never published. No contact with the creators.
6. Derived cells that describe a single person are suppressed in public outputs.
