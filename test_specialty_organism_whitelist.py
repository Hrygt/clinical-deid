"""Specialty-noun + organism-vocabulary whitelist tests (fix/specialty-whitelist,
grader report d75ee47a6443).

Witnessed defect: "The case was discussed with podiatry." de-identified to
"...discussed with Patricia." The trigger is the name-likely frame ("discussed with
<Capitalized>", "<Specialty> consulted"); medical_whitelist.py contained ZERO
specialty words, so nothing could veto. A specialty token de-id has already deleted
is unrecoverable by any downstream grader vocabulary (corpus/README.md
cat3-podiatry-token) — the Cat 3 externality axis reads exactly these words.

Organism sibling, same mechanism: the NER reads a binomial as First+Last and
surrogates the species epithet as a surname — "Enterobacter cloacae" ->
"Enterobacter gonzalez" (gold 87a23c58a070 / report 87c3e2001703), "Proteus
mirabilis" -> "Eric Terry" (reproduced live 2026-07-27).

PHI ASYMMETRY is the binding constraint: a whitelisted token survives redaction
EVERYWHERE, so every addition ships with a LEAK COUNTER-PROBE proving a genuine
name in the SAME frame still redacts (section 3). Admission rule: nouns only, no
plausible person name, faker-checked; exclusions are documented in
medical_whitelist.py (endo / cards / all 2-3 letter abbreviations / candida /
providencia).

Span layer, NO model / NO GPU (DEID_SKIP_MODEL_LOAD). The live model witnesses are
run separately as gate artifacts (scratchpad live probe), since a suite may not
depend on a GPU.

Run:  python test_specialty_organism_whitelist.py
"""
import io
import os
import re
import sys
from contextlib import redirect_stdout

os.environ.setdefault("DEID_SKIP_MODEL_LOAD", "1")

from api import filter_whitelisted_entities  # noqa: E402
from deid import deidentify_text  # noqa: E402
from medical_whitelist import MEDICAL_WHITELIST_LOWER  # noqa: E402

SEED = 42
CASES = []


def case(name, fn):
    CASES.append((name, fn))


def _ents(src, spans):
    out = []
    for frag, etype, occ in spans:
        idx = -1
        for _ in range(occ + 1):
            idx = src.find(frag, idx + 1)
        assert idx >= 0, f"{frag!r} not in {src!r}"
        out.append({"type": etype, "start": idx, "end": idx + len(frag), "text": frag})
    return out


def _survives(src, spans, must_survive, must_redact=()):
    """Filter + replace; assert the clinical token survives and any real name doesn't."""
    ents = filter_whitelisted_entities(_ents(src, spans))
    buf = io.StringIO()
    with redirect_stdout(buf):
        out = deidentify_text(src, [dict(e) for e in ents], SEED)
    kept = [w for w in must_survive if re.search(rf"(?<![A-Za-z]){re.escape(w)}(?![A-Za-z])", out)]
    leaked = [w for w in must_redact if re.search(rf"(?<![A-Za-z]){re.escape(w)}(?![A-Za-z])", out)]
    ok = len(kept) == len(must_survive) and not leaked
    return ok, f"out={out!r} survived={kept} leaked={leaked}"


# ---- 1. Specialty nouns in the witnessed frame (red on HEAD: surrogated) ----
def _d75e_witness():
    # The d75e two-sentence original, BOTH podiatry instances, as the model tags them
    # (live: sentence-initial "Podiatry" -> FIRST_NAME).
    src = ("Based on previous cultures, will discontinue Zosyn and continue vancomycin. "
           "The case was discussed with Podiatry. Podiatry will be consulting on the patient.")
    return _survives(src, [("Podiatry", "FIRST_NAME", 0), ("Podiatry", "FIRST_NAME", 1)],
                     must_survive=["Podiatry"])
case("1a GATE d75e: both podiatry instances survive [must survive]", _d75e_witness)


def _frames():
    probes = [
        ("Discussed with Cardiology, they recommend beta blockade.", "Cardiology", "FIRST_NAME"),
        ("Nephrology consulted. Avoid nephrotoxic meds.", "Nephrology", "FIRST_NAME"),
        ("Spoke with Urology about the obstruction.", "Urology", "LAST_NAME"),
        ("Consulted Pulmonology for the effusion.", "Pulmonology", "FIRST_NAME"),
        ("Discussed with Neurology overnight.", "Neurology", "FIRST_NAME"),
        ("Case discussed with Psychiatry today.", "Psychiatry", "LAST_NAME"),
        ("Contacted Nutrition for supplementation.", "Nutrition", "FIRST_NAME"),
        ("Coordinated with Hospice for transition.", "Hospice", "LAST_NAME"),
        ("Discussed with Podiatry about the ulcer.", "Podiatry", "FIRST_NAME"),
    ]
    bad = []
    for src, tok, typ in probes:
        ok, ev = _survives(src, [(tok, typ, 0)], must_survive=[tok])
        if not ok:
            bad.append(f"{tok}: {ev}")
    return (not bad, f"{len(probes) - len(bad)}/{len(probes)} specialty tokens survive; fails={bad}")
case("1b specialty nouns in discussion frames survive [must survive]", _frames)


def _bigram():
    src = "Discussed with Wound Care regarding the sacral ulcer."
    return _survives(src, [("Wound", "FIRST_NAME", 0), ("Care", "LAST_NAME", 0)],
                     must_survive=["Wound Care"])
case("1c service bigram 'Wound Care' survives (adjacent-pair path) [must survive]", _bigram)


def _bigram_single_span():
    src = "Per Case Management, SNF placement pending."
    return _survives(src, [("Case Management", "NAME", 0)], must_survive=["Case Management"])
case("1d service bigram as ONE span survives [must survive]", _bigram_single_span)


# ---- 2. Organism vocabulary (red on HEAD: 'Proteus mirabilis' -> 'Eric Terry') ----
def _organisms():
    probes = [
        ("Urine culture growing Proteus mirabilis.", [("Proteus", "FIRST_NAME", 0),
         ("mirabilis", "LAST_NAME", 0)], ["Proteus", "mirabilis"]),
        ("Growing Enterobacter cloacae on repeat culture.", [("Enterobacter", "FIRST_NAME", 0),
         ("cloacae", "LAST_NAME", 0)], ["Enterobacter", "cloacae"]),
        ("Blood cultures positive for Staphylococcus aureus.", [("aureus", "LAST_NAME", 0)],
         ["aureus"]),
        ("Bacteremia due to Klebsiella pneumoniae.", [("Klebsiella", "FIRST_NAME", 0),
         ("pneumoniae", "LAST_NAME", 0)], ["Klebsiella", "pneumoniae"]),
        ("Wound grew Morganella morganii.", [("Morganella", "FIRST_NAME", 0),
         ("morganii", "LAST_NAME", 0)], ["Morganella", "morganii"]),
        ("Stool positive for Clostridioides difficile.", [("difficile", "LAST_NAME", 0)],
         ["difficile"]),
    ]
    bad = []
    for src, spans, survive in probes:
        ok, ev = _survives(src, spans, must_survive=survive)
        if not ok:
            bad.append(f"{survive}: {ev}")
    return (not bad, f"{len(probes) - len(bad)}/{len(probes)} organism names survive; fails={bad}")
case("2a binomials survive intact [must survive]", _organisms)


def _candida_excluded():
    # Deliberate exclusion: "Candida" is a real given name -> NOT whitelisted; the
    # epithet still is, so the binomial degrades rather than garbling into two names.
    genus_in = "candida" in MEDICAL_WHITELIST_LOWER
    epithet_in = "albicans" in MEDICAL_WHITELIST_LOWER
    return (not genus_in and epithet_in,
            f"candida whitelisted={genus_in} (must be False) albicans={epithet_in} (must be True)")
case("2b 'candida' deliberately NOT whitelisted, 'albicans' is [asymmetry]", _candida_excluded)


def _excluded_tokens():
    # "pt" is NOT listed: "Pt" is a PRE-EXISTING role word (patient) in the file's role
    # block, admitted long before this branch and out of scope for the specialty rule.
    banned = ["endo", "cards", "id", "gi", "pa", "ot", "cm", "ir", "rd",
              "rt", "slp", "pcp", "cts", "ent", "providencia"]
    present = [t for t in banned if t in MEDICAL_WHITELIST_LOWER]
    return (not present, f"wrongly whitelisted={present} [must stay empty]")
case("2c collision-prone tokens stay OUT of the whitelist [must stay empty]", _excluded_tokens)


# ---- 3. LEAK COUNTER-PROBES — genuine names in the same frames MUST redact ----
def _leak_patricia():
    src = "Discussed with Patricia."
    return _survives(src, [("Patricia", "FIRST_NAME", 0)],
                     must_survive=[], must_redact=["Patricia"])
case("3a LEAK 'Discussed with Patricia.' still redacts [must stay empty]", _leak_patricia)


def _leak_patricia_paren():
    src = "Discussed with Patricia Smith (podiatry)."
    ok, ev = _survives(src, [("Patricia", "FIRST_NAME", 0), ("Smith", "LAST_NAME", 0)],
                       must_survive=["podiatry"], must_redact=["Patricia", "Smith"])
    return ok, ev
case("3b LEAK 'Patricia Smith (podiatry)' — names redact, parenthetical survives",
     _leak_patricia_paren)


def _leak_specialty_frame_name():
    src = "Cultures reviewed with Dr. Sanders; growing Staphylococcus aureus."
    return _survives(src, [("Sanders", "LAST_NAME", 0)],
                     must_survive=["aureus"], must_redact=["Sanders"])
case("3c LEAK genuine surname in an ORGANISM frame still redacts [must stay empty]",
     _leak_specialty_frame_name)


def _leak_consult_name():
    src = "Nephrology consulted; spoke with Dr. Whitfield directly."
    return _survives(src, [("Whitfield", "LAST_NAME", 0)],
                     must_survive=["Nephrology"], must_redact=["Whitfield"])
case("3d LEAK genuine surname beside a surviving specialty [must stay empty]",
     _leak_consult_name)


def _leak_patient_name_elsewhere():
    # The patient's own name in a header must still redact with specialties whitelisted.
    src = "Patient: Marcus Delgado\nDiscussed with Podiatry about the wound."
    return _survives(src, [("Marcus", "FIRST_NAME", 0), ("Delgado", "LAST_NAME", 0)],
                     must_survive=["Podiatry"], must_redact=["Marcus", "Delgado"])
case("3e LEAK patient name redacts while specialty survives [must stay empty]",
     _leak_patient_name_elsewhere)


# ---- 4. No-regression: existing whitelist behavior unchanged ----
def _existing_kept():
    for t in ("propranolol", "bradycardia", "cefepime", "ativan"):
        if t not in MEDICAL_WHITELIST_LOWER:
            return (False, f"pre-existing entry {t!r} lost")
    return (True, "propranolol/bradycardia/cefepime/ativan all still present")
case("4a pre-existing whitelist entries intact [must hold]", _existing_kept)


def _no_dupes():
    from medical_whitelist import MEDICAL_WHITELIST
    lowered = [t.lower() for t in MEDICAL_WHITELIST]
    dupes = {t for t in lowered if lowered.count(t) > 1}
    return (not dupes, f"case-insensitive duplicates={sorted(dupes)} [must stay empty]")
case("4b no case-insensitive duplicate entries [must stay empty]", _no_dupes)


def main():
    print("=" * 104)
    print("SPECIALTY + ORGANISM WHITELIST - span-layer evidence table")
    print(f"whitelist size: {len(MEDICAL_WHITELIST_LOWER)} lowered entries")
    print("=" * 104)
    print(f"{'case':72s} {'status':6s} evidence")
    print("-" * 104)
    failures = 0
    for name, fn in CASES:
        try:
            ok, ev = fn()
        except AssertionError as exc:
            ok, ev = False, f"setup assert: {exc}"
        except Exception as exc:  # noqa: BLE001
            ok, ev = False, f"error: {exc}"
        if not ok:
            failures += 1
        print(f"{name:72s} [{'PASS' if ok else 'FAIL'}] {ev}")
    print("-" * 104)
    print(f"{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
