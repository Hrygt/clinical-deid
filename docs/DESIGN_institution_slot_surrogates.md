# Design memo — institution-slot surrogates

**Status: DESIGN ONLY. Nothing built. HOLD for Gary's ruling.**
Session 2026-07-27 (clinical-deid), Task 3. Companion branches (also at HOLD):
`fix/name-span-newline-clip`, `fix/specialty-whitelist`.

## The defect

Facility / institution names are surrogated as **person first names**, inconsistently.
Witnesses (8+ across 7 notes, 3 stores): "TEE report from Larry / Nicole / Shawnee /
Jacqueline" — four different surrogates for **one** source facility across sibling notes;
"per Shawnee providers"; "Per Jennifer Complex Care Coordination".

The damage is **surrogate-TYPE miscategorization garbling meaning**, not a redaction
failure. The facility *is* removed. What is lost is that the reader (and the grader) can no
longer tell an institution from a person — "per Kenneth providers" reads as a clinician.

## (a) Root cause — where the entity type is decided, and why institution slots land on person

Three facts, each verified in code and reproduced live on the local model (2026-07-27):

**1. There is no institution type in the label space at all.** `labels.py` defines
`ENTITY_TYPES` as exactly 25 types (`labels.py:4-39`) — names, contact, geo, dates, IDs,
age. There is no `ORGANIZATION`, `FACILITY`, `HOSPITAL`, or `EMPLOYER`. The training-label
bridge has none either (`NEMOTRON_TO_ENTITY`, `labels.py:61-87`): the model was trained on
Nemotron-PII, whose schema has no organization class. The BILOU head therefore has **101
labels, none of which can express "this is an institution."**

**2. So the slot scatters to whichever wrong type is nearest** — this is the real finding,
and it corrects the framing that institutions land specifically on person names. Six live
probes produced **four different wrong types**:

| probe | model tag | output |
|---|---|---|
| `TEE report from Shawnee Regional Medical Center` | `FIRST_NAME` "TEE" + `COUNTY` "Shawnee Regional" | `SUSAN report from Ibarrahaven County Medical Center` |
| `Continue plan per Shawnee providers.` | `FIRST_NAME` "Shawnee" | `Continue plan per Kenneth providers.` |
| `transferred from Jane Phillips Medical Center` | `FIRST_NAME` + `LAST_NAME` | `transferred from Jessica Mullins Medical Center` |
| `Records requested from Bellevue Skilled Nursing Facility` | `STREET_ADDRESS` "Bellev" | `Records requested from 4947 John Oval Suite 873 Skilled Nursing Facility.` |
| `seen at St. Mary's Hospital` | `STREET_ADDRESS` | `seen at 35713 Derrick Path Suite 043` |
| `Per Complex Care Coordination, placement pending.` | (none) | unchanged |

Person-name is simply the **most damaging** landing spot, not the only one. `STREET_ADDRESS`
garbles just as badly ("St. Mary's Hospital" → a street address). Any fix scoped to
"person-typed facilities" would close under half of the class.

**3. The surrogate class follows mechanically from the type.** `ClinicalDeidentifier.replace`
dispatches on `entity_type` (`deid.py:380-481`): `FIRST_NAME` → `_fake_first` →
`faker.first_name()`, `STREET_ADDRESS` → `_generate_street`, `COUNTY` → `city + " County"`.
Once the type is wrong the surrogate class is wrong; there is no later stage that could
notice.

**Why inconsistent across sibling notes.** `deidentify_text` constructs a **fresh**
`ClinicalDeidentifier` per call and calls `reset_cache()` (`deid.py:1301-1302`), and the
per-token caches are per-instance (`deid.py:221-239`). Consistency is **per-document by
design**; `seed` is per-request and normally `None`. Live confirmation — the same input, four
separate requests: `North Ashleyhaven`, `Port Sherribury`, `Mooreborough`, `Davidchester`.
So the "four surrogates for one source" is not a cache bug. It is the deliberate scope, and
it is *load-bearing*: a cross-document mapping is exactly what a re-identification table is.

## (b) Options

### Option 1 — Facility-class surrogates via span-layer type correction *(no retrain)*

An institution recognizer runs at the span layer, after detection, and **retypes** (never
drops) any entity whose span sits in an institution slot — anchored on facility head-nouns
(`Hospital`, `Medical Center`, `Clinic`, `Skilled Nursing Facility`, `Rehab`, `Health
System`, `Nursing Home`) and on institution frames (`transferred from X`, `records from X`,
`per X providers`, `seen at X`). A new `FACILITY` branch in `replace()` emits a
facility-shaped surrogate.

*Leak risk: **neutral — structurally.*** This is the decisive property. The span is still
detected and still replaced; only the *shape* of the replacement changes. No whitelist, no
veto, no drop. Retyping cannot make a real name survive, because the retyped span is
surrogated either way. The one rule that must be enforced in code and pinned in tests: the
recognizer may **only ever change `type`**, never remove an entity and never shrink a span.

*Residual risk:* facility names frequently **contain real person names** ("Jane Phillips
Medical Center"). This is fine and must stay fine — retyping the span to `FACILITY` still
replaces "Jane Phillips", so the real person's name does not survive. It does mean the
surrogate must not preserve the original's internal tokens.

*Cost:* moderate; a recognizer + one surrogate generator + a pinned test suite. No model
change, no retrain, no data.

### Option 2 — Consistent per-source surrogate mapping (cross-note stability)

Persist `original facility → surrogate` so all sibling notes agree.

*Leak risk: **HIGH, and disqualifying.*** The store would be a durable table mapping real
institution names to their surrogates — a re-identification key by construction. It breaks
the system's standing invariant that raw/PHI text never persists (the same invariant that
makes the report store and gold corpus safe to read freely). It would also be the first
cross-document state in the pipeline, and it would have to be keyed on the raw string, i.e.
on PHI. **Recommend against on privacy grounds, independent of effort.**

*Note:* the problem it targets largely dissolves under Option 3.

### Option 3 — Type correction to a **class-generic** surrogate (Option 1, with the surrogate chosen to make consistency moot)

Same recognizer as Option 1, but the surrogate is deliberately **generic rather than a
specific fake institution**: "an outside facility", "Outside Hospital", "an outside skilled
nursing facility" — matched to the head noun.

*Why this is more than a cosmetic variant of Option 1:* a class-generic surrogate is
**identical in every note without any persistent map**. "TEE report from an outside
facility" reads correctly in all four sibling notes, and the fact that they were the *same*
outside facility was never recoverable from the de-identified text anyway. It delivers
Option 2's semantic benefit at zero privacy cost, and it removes the temptation to build a
mapping store later.

*Trade-off:* it discards the (fake) distinctness between two *different* outside facilities
in one note. That distinctness is currently fictional and unreliable, so little is lost; if a
note genuinely distinguishes two facilities, a per-document counter ("Outside Hospital A/B")
recovers it inside the existing per-document scope.

*Leak risk:* same as Option 1 — neutral, for the same structural reason.

## (c) Recommendation

**Option 3.** Span-layer type correction, retype-only, with class-generic facility
surrogates; explicitly **reject Option 2**.

Reasons, in order of weight:

1. **It is leak-neutral by construction**, which is the only property that matters under the
   PHI asymmetry rule. It adds no whitelist and no veto — nothing in it can let a real name
   survive, and that claim is structural rather than empirical.
2. **It covers the whole class.** The live probes show institutions landing on `FIRST_NAME`,
   `LAST_NAME`, `COUNTY`, and `STREET_ADDRESS`; a slot-anchored recognizer catches all four,
   where a person-name-only fix would catch under half.
3. **It kills the consistency complaint without a mapping store** — the one option that
   improves cross-note readability while *reducing* rather than increasing re-identification
   surface.
4. **No retrain.** Adding `ORGANIZATION` to the label space is the principled long-term fix,
   but it means a 101→105 label head, annotated institution data the project does not have,
   and a full revalidation against the 98.4% recall baseline. It belongs on the recognizer
   campaign roadmap, not in this fix. Option 3 does not conflict with it — the recognizer
   becomes redundant, not wrong, if the model later learns the type.

**Gates this fix should be held to if ruled in** (none run — nothing is built):
constructed institution-slot probes across all four observed mis-types; a retype-only
invariant test (entity count and every span offset unchanged; only `type` differs); a leak
counter-probe proving a genuine clinician name in the same frame still redacts
("transferred from Jane Phillips Medical Center by Dr. Whitfield"); `deid_score` recall
unchanged at the 98.4% / FIRST 99.5 / LAST 99.6 baseline; and — because the honesty flag is
blind to this class — a constructed before/after diff, never the flag.

**Open question for the ruling:** whether the grader wants institution identity *at all*.
If any Data/Risk axis reads "outside facility" as an externality signal, Option 3's generic
surrogate is strictly better than today's fake person name; if some axis needs to distinguish
two named institutions, say so before this is built, because that requirement would push
toward the per-document A/B counter variant.
