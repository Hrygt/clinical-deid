# clinical-deid backlog

Follow-up ledger. Opened 2026-07-05 after the fusion-fix batch merge
(tag deploy-2026-07-05-fusion-batch, payload SHA 12b89297).

## SESSION BOARD 2026-07-27 — three defect classes (two built, one designed)

**Everything below is at HOLD. Nothing merged, nothing deployed. Awaiting Gary.**

Standing constraint honored throughout: the reid honesty flag is BLIND to
deletion-class damage (surrogates insert cleanly, `skipped_unmatched=0`), so every gate
used **constructed probes**, never the flag.

| branch | class | state | gate evidence |
|---|---|---|---|
| `fix/name-span-newline-clip` | NAME spans crossing line breaks (SPAN layer) | built, HOLD | new suite 15/15 (3/15 red on HEAD); battery 10 suites green; gold survival 166/166; deployed grade Moderate |
| `fix/specialty-whitelist` | specialty + organism words surrogated as names | built, HOLD | new suite 14/14 (7/14 red on HEAD); battery green; recall 98.4% == baseline |
| `docs/institution-slot-memo` | institution slots surrogated as person names | DESIGN ONLY, no build | `docs/DESIGN_institution_slot_surrogates.md` |

### Task 1 — newline over-expansion, SPAN-layer half
The 2026-07-19 fix (b8f0298d) closed the **recall-regex** half only. Live probing on
clean main found the residual: the **model itself** emits cross-newline `*_NAME` spans
("Sarah\nJohnson" signature blocks; "\nWhitaker" which fragment repair expands to
"Jonathan\nWhitaker"), and `_combine_adjacent_name_entities` glued name entities across
a bare newline. Replacement then deletes the line break and fuses the lines. Fix:
`api._clip_name_spans_at_line_breaks` (retype/split, whitelist belt) + combine gap guard
+ `_split_name_spans` cuts at line breaks.

Gate results: (a) wrapped GENUINE surname zero-leak post-clip; (b) gold scan — 90 exposed
notes / 178 swept instances, **166/166 clinical tokens survive**, and the other 12 are
signature-block person names (`Lisa Johnson, MD`) that are *supposed* to be redacted —
the census regex cannot tell the two apart, the manual read can; (c) witness 466697e91ec0
preserves Propranolol + the Bradycardia header; (d) deployed grade (engine v2026.07.27.1)
**Risk Moderate**, restored CCPM as lead evidence.

### Task 2 — specialty-word / organism NER false positive
Report d75ee47a6443. Census first (read-only, gold 918 + reports 77 + accuracy 425): 58
distinct specialty tokens in ~330 discussion frames, "Podiatry" Title-cased 8/8. Organism
sibling is the same mechanism. Added 60 specialty nouns + 7 clipped forms + 16 bigrams +
19 genera + 45 epithets, all faker-checked.

**KNOWN RESIDUAL, must be read before ruling:** a whitelisted token survives redaction
EVERYWHERE — "Discussed with Dr. Aureus" now survives (probed). Accepted only because no
admitted token is a plausible person name; that judgement IS the control, which is why
`endo` (Japanese surname), `cards`, `candida`/`providencia` (real given names) and all
2-3 letter abbreviations were excluded. Sub-token glueing ("Klebsiella pneumoniajones")
is NOT closed by vocabulary — it is the NER span-fragment problem.

**Parked:** frame-gated veto for the high-collision abbreviations (ID/GI/PA/OT/CM/IR/...).
The whitelist is a context-free exact-match filter and cannot express a frame condition.

### Step-0 findings (both answered, and one is load-bearing)

1. **Raw source texts are NOT retained** in any of the three stores, so the corrupted
   stored evidence is **PERMANENT** and no re-deid backfill is possible. Accuracy items
   keep `note_sha256` + `deid_note` only (`accuracy/store.py:2-6, 337-342`); raw goes to
   `accuracy-originals` with a **24h TTL**, hard-deleted at first PHI render
   (`originals.py:129-146`, `views.py:205-209`). The report store never receives raw
   (`cpt/reports.py:16-18`). Gold holds deid text only (`corpus/README.md:11-21`) and
   `build_corpus.py` reads already-deid sources. Only re-deid window: a batch graded in
   the last 24h and never PHI-rendered. The one raw archive that exists anywhere belongs
   to a different pipeline (extraction S3, `extraction/store.py:621-628`).
2. **The accuracy reporters REPLAY stored grades; they never regrade.** `report.py:790-792`
   reads the stored verdict, `gap.analyze` is pure, and `engine_client` is not imported
   anywhere in the reporting path. So a de-id fix does **not** change any number already
   shown to a physician — it changes only the evidence trail going forward. *But* three
   portal-side layers DO recompute over the stored deid text at every render (clone gate
   `report.py:787`, time-scope `report.py:800-820`, Cat 2/3 refinement `report.py:812`),
   so de-id artifacts in stored text still distort those.

### Deploy-state repair done this session (bookkeeping only, no code shipped)
Prod code matched main byte-for-byte (`api.py` / `deid.py` / `medical_whitelist.py` md5),
but **two pointers were stale at the previous SHA `4a3889e1`**: the S3 reconcile pin
(`clinical-deid/deploy/TARGET_SHA`) and the `VERSION` file (S3 substrate + on-box). A
relaunch would have rolled prod BACK past the 2026-07-19 newline fix. Both moved to
`97b6d726`. Two related findings for the ledger:
- `/deid/health` reported the stale SHA, so **the health SHA can lie about the running
  code** — it reads a file the deploy writes, not the code.
- The box has **no `clinical-deid-reconcile.service`**. The live bootstrap
  (`s3://.../deploy/bootstrap.sh`) uses an `aws s3 sync` substrate and never installs the
  reconcile unit from `user-data-both.sh`. `reconcile.sh` is therefore **dead code on prod**
  and the S3 pin is advisory, not enforced. Decide: install the unit, or delete the script
  and pin the substrate instead. **Owner: Gary.**

## Branch 7: ZIP-prefix backstop extension (full-run tag over a ZIP+4 tail)

Branch 2's R3 sub-run insurance drops a ZIP+4 tail only when the NER tags a proper
SUB-run of the +4 (the real pilot's "25" of "9625"). When the NER tags the ENTIRE +4
run as an identifier, R3 does not fire (it is not a sub-run), the +4 is surrogated as
"MRN<digits>", and the Branch 5 backstop cannot re-generalize "74804-<letters>", so the
5-digit ZIP prefix survives. No real pilot note exhibits this; surfaced by the post-deploy
synthetic round trip.

Red seed: input "SHAWNEE OK 74804-9638" with the NER tagging the full "9638" as
MEDICAL_RECORD_NUMBER produces "74804-MRN1043" (74804 leaks). Fix direction: extend R3 (or
the Branch 5 backstop) to drop / re-generalize a full-run identifier tag that is the +4 of
a ZIP+4, so the ZIP backstop owns the whole ZIP. Owner: recognizer campaign.

## ASG schedule discrepancy (flag for Gary)

The starter doc / runbook notes describe a nightly 1-to-0 scale-down of the clinical-deid
box at 23:00. The actual ASG `cpt-dnn-service-asg` (instance i-09bb5c4ce5fa0a55f) has NO
scheduled actions (account-wide, none), Min 0 / Max 1 / Desired 1, one instance running
24/7. Decision needed: is the box intended to run 24/7 (then the doc is stale and the
"07:00-23:00 window" is advisory only), or should a nightly scale-down be (re)added to cut
GPU cost? 24/7 GPU cost vs stale doc. Owner: Gary.

## Accuracy Reporter: tabular-fusion residual retirement

The grader's scan_fusion "tabular_fusion" signature was a residual-detection heuristic for
the DATE-in-tabular class. With the batch at zero fusion signatures on the 21-note pilot,
retire (or downgrade) the tabular-fusion residual check once the first full 650-note batch
runs clean through the deployed service. Pending: first clean 650-batch. Owner: grader.

## NER detection errors neutralized at the span layer, not fixed at detection

This session's span-layer passes (Branches 1/2/6) neutralize several NER mis-tags AFTER
detection, so the outputs are clean, but the underlying detection errors remain and should
be fixed at the model / recognizer level:

- full ZIP+4 tail ("9638") tagged MEDICAL_RECORD_NUMBER
- "SH" (prefix of "SHAWNEE") tagged EMPLOYEE_ID
- procedure names ("ESOPHAGOGASTRODUODENOSCOPY") tagged UNIQUE_ID
- room tokens ("RM06"/"RM08") tagged POSTCODE

Owner: recognizer campaign (structured recognizers + SAFE library) and the ModernBERT
Phase 2 data argument (more Epic-tabular training data to teach the model these are not
identifiers).
