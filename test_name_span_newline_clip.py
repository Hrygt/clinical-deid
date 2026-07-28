"""NAME-span newline-clip tests (fix/name-span-newline-clip — the SPAN-LAYER half of
the 2026-07-19 newline ruling; the recall-regex half shipped as
fix/name-span-newline-boundary, b8f0298d).

Residual defect (probed live on HEAD, local model, 2026-07-27): the NER model itself
emits *_NAME spans that cross a line break ("Sarah\\nJohnson" in a signature block;
"\\nWhitaker", which fragment repair then expands to "Jonathan\\nWhitaker"), and
deid.py's _combine_adjacent_name_entities glues two name entities across a bare
newline (gap regex uses \\s). Surrogate replacement of such a span DELETES the line
break — two lines fuse, and any line-leading clinical token the model swept is
destroyed exactly like the witnessed recall-net damage (grader note 466697e91ec0:
"Dr Trac[y]\\nPropranolol" -> "Dr Bradley Anderson").

Ruled fix under test: a *_NAME span must never cross a line break —
  * api._clip_name_spans_at_line_breaks: split at [\\r\\n]+ into per-line pieces;
    each piece stays an entity of the same type (a GENUINE wrapped name still
    redacts per-line — PHI ASYMMETRY: no fix may let a real name survive);
    whitelist belt: a piece whose word is in MEDICAL_WHITELIST_LOWER is DROPPED so
    the clinical token survives (fragment-repair doctrine — fix drug loss by
    whitelist ADDITION, never by weakening the guard).
  * deid._combine_adjacent_name_entities: the combine gap must never contain a
    line break (horizontal whitespace only, same doctrine as _TITLE_RE/_CRED_RE).
  * deid._split_name_spans: belt at the replacement layer — cuts at line breaks
    too, so a cross-newline span reaching deidentify_text from ANY caller is
    split and the line break survives replacement.

Span layer, NO model / NO GPU (DEID_SKIP_MODEL_LOAD). Modeled on
test_name_span_fragment_repair.py.

Run:  python test_name_span_newline_clip.py
"""
import io
import os
import re
import sys
from contextlib import redirect_stdout

os.environ.setdefault("DEID_SKIP_MODEL_LOAD", "1")

from deid import (  # noqa: E402
    deidentify_text,
    _combine_adjacent_name_entities,
    _split_name_spans,
)

try:
    from api import _clip_name_spans_at_line_breaks as _clip  # the fix
    HAVE_CLIP = True
except Exception:  # noqa: BLE001
    _clip = None
    HAVE_CLIP = False

SEED = 42
CASES = []


def case(name, fn):
    CASES.append((name, fn))


def _ents(src, spans):
    """spans: list of (fragment, type, occ). Builds NER-like entities by offset."""
    out = []
    for frag, etype, occ in spans:
        idx = -1
        for _ in range(occ + 1):
            idx = src.find(frag, idx + 1)
        assert idx >= 0, f"{frag!r} not in {src!r}"
        out.append({"type": etype, "start": idx, "end": idx + len(frag), "text": frag})
    return out


def _spans(res, src):
    return [src[e["start"]:e["end"]] for e in res]


def _deid(src, ents):
    buf = io.StringIO()
    with redirect_stdout(buf):
        out = deidentify_text(src, [dict(e) for e in ents], SEED)
    return out


# ---- 1. Clip function exists and splits (MUST SPLIT; red on HEAD: no clip) ----
def _clip_exists():
    return (HAVE_CLIP, "api._clip_name_spans_at_line_breaks importable" if HAVE_CLIP
            else "MISSING on HEAD (fix not built)")
case("1a clip function exists [must exist]", _clip_exists)


def _clip_splits():
    if not HAVE_CLIP:
        return (False, "clip missing")
    src = "Signed: Sarah\nJohnson, RN"
    res = _clip(src, _ents(src, [("Sarah\nJohnson", "LAST_NAME", 0)]))
    got = _spans(res, src)
    return (got == ["Sarah", "Johnson"], f"pieces={got}")
case("1b cross-newline span splits to per-line pieces [must split]", _clip_splits)


def _clip_types_kept():
    if not HAVE_CLIP:
        return (False, "clip missing")
    src = "brother Jonathan\nWhitaker agrees"
    res = _clip(src, _ents(src, [("Jonathan\nWhitaker", "LAST_NAME", 0)]))
    ok = all(e["type"] in ("FIRST_NAME", "LAST_NAME", "NAME") for e in res) and len(res) == 2
    return (ok, f"pieces={[(e['type'], e['text']) for e in res]}")
case("1c pieces keep NAME-family type (stay redactable) [must keep]", _clip_types_kept)


def _clip_crlf_multiline():
    if not HAVE_CLIP:
        return (False, "clip missing")
    src = "Dr. Mccoy\r\nBradycardia\r\nPresent"
    res = _clip(src, _ents(src, [("Mccoy\r\nBradycardia\r\nPresent", "NAME", 0)]))
    got = _spans(res, src)
    # Bradycardia is whitelisted (belt) -> dropped; Mccoy + Present stay entities.
    return (got == ["Mccoy", "Present"], f"pieces={got} (Bradycardia must be dropped)")
case("1d CRLF 3-line span: whitelisted middle piece dropped [belt]", _clip_crlf_multiline)


def _clip_whitelist_drop():
    if not HAVE_CLIP:
        return (False, "clip missing")
    src = "See Dr Tracy\nPropranolol is held."
    res = _clip(src, _ents(src, [("Tracy\nPropranolol", "NAME", 0)]))
    got = _spans(res, src)
    return (got == ["Tracy"], f"pieces={got} (Propranolol whitelisted -> dropped, survives)")
case("1e witnessed shape: drug piece dropped via whitelist [must survive]", _clip_whitelist_drop)


def _clip_untouched():
    if not HAVE_CLIP:
        return (False, "clip missing")
    src = "Dr John Smith saw the patient."
    ents = _ents(src, [("John Smith", "NAME", 0)])
    res = _clip(src, [dict(e) for e in ents])
    got = _spans(res, src)
    return (got == ["John Smith"], f"pieces={got}")
case("1f single-line multi-word span untouched [must not touch]", _clip_untouched)


def _clip_non_name():
    if not HAVE_CLIP:
        return (False, "clip missing")
    src = "DOB: 01/02/1960\n70 year old"
    ents = [{"type": "DATE_OF_BIRTH", "start": 5, "end": 20, "text": src[5:20]}]
    res = _clip(src, [dict(e) for e in ents])
    ok = len(res) == 1 and res[0]["start"] == 5 and res[0]["end"] == 20
    return (ok, f"res={_spans(res, src)} (non-NAME types out of scope)")
case("1g non-NAME cross-newline span untouched [out of scope]", _clip_non_name)


# ---- 2. combine gap must never contain a line break (red on HEAD: glues) ----
def _combine_glue():
    src = "See Tracy\nPropranolol held."
    ents = _ents(src, [("Tracy", "LAST_NAME", 0), ("Propranolol", "FIRST_NAME", 0)])
    res = _combine_adjacent_name_entities([dict(e) for e in ents], src)
    crossers = [src[e["start"]:e["end"]] for e in res
                if "\n" in src[e["start"]:e["end"]] or "\r" in src[e["start"]:e["end"]]]
    return (not crossers, f"cross-newline combined spans={crossers} [must stay empty]")
case("2a combine never glues across a bare newline [must stay empty]", _combine_glue)


def _combine_glue_indent():
    src = "Contact: Sarah\n   Johnson RN"
    ents = _ents(src, [("Sarah", "FIRST_NAME", 0), ("Johnson", "LAST_NAME", 0)])
    res = _combine_adjacent_name_entities([dict(e) for e in ents], src)
    crossers = [src[e["start"]:e["end"]] for e in res
                if "\n" in src[e["start"]:e["end"]]]
    return (not crossers, f"cross-newline combined spans={crossers} [must stay empty]")
case("2b combine never glues across newline+indent [must stay empty]", _combine_glue_indent)


def _combine_same_line_kept():
    src = "Seen by Sarah Johnson today."
    ents = _ents(src, [("Sarah", "FIRST_NAME", 0), ("Johnson", "LAST_NAME", 0)])
    res = _combine_adjacent_name_entities([dict(e) for e in ents], src)
    got = _spans(res, src)
    return (got == ["Sarah Johnson"], f"spans={got}")
case("2c same-line combine still works [must combine]", _combine_same_line_kept)


# ---- 3. replacement-layer belt: _split_name_spans cuts at line breaks ----
def _splitter_newline():
    src = "Signed: Sarah\nJohnson, RN"
    ents = _ents(src, [("Sarah\nJohnson", "NAME", 0)])
    res = _split_name_spans([dict(e) for e in ents], src)
    got = _spans(res, src)
    return (got == ["Sarah", "Johnson"], f"pieces={got}")
case("3a _split_name_spans cuts at newline [must cut]", _splitter_newline)


def _splitter_initial_kept():
    src = "Patient of A. Grant, MD."
    ents = _ents(src, [("A. Grant", "NAME", 0)])
    res = _split_name_spans([dict(e) for e in ents], src)
    got = _spans(res, src)
    return (got == ["A. Grant"], f"pieces={got} (initials preserved, no regression)")
case("3b middle-initial span still NOT cut [must not cut]", _splitter_initial_kept)


# ---- 4. E2E replacement: line break SURVIVES, both lines still redacted ----
def _e2e_structure():
    src = "Plan reviewed.\nSigned: Sarah\nJohnson, RN"
    ents = _ents(src, [("Sarah\nJohnson", "LAST_NAME", 0)])
    out = _deid(src, ents)
    lines_kept = out.count("\n") == src.count("\n")
    redacted = not re.search(r"\bSarah\b|\bJohnson\b", out)
    return (lines_kept and redacted,
            f"out={out!r} lines {out.count(chr(10))}/{src.count(chr(10))} redacted={redacted}")
case("4a wrapped-name replacement keeps the line break [must keep+redact]", _e2e_structure)


def _e2e_leak_probe():
    # GATE (a): a GENUINE surname continuing on the next line must NOT leak post-clip.
    src = "Seen with brother Jonathan\nWhitaker at bedside."
    ents = _ents(src, [("Jonathan\nWhitaker", "LAST_NAME", 0)])
    out = _deid(src, ents)
    leak = re.search(r"\bJonathan\b|\bWhitaker\b", out)
    return (not leak, f"out={out!r} leak={bool(leak)} [must stay empty]")
case("4b GATE(a) wrapped GENUINE name: zero leak post-clip [must stay empty]", _e2e_leak_probe)


def _e2e_idempotent():
    if not HAVE_CLIP:
        return (False, "clip missing")
    src = "Signed: Sarah\nJohnson, RN"
    ents = _ents(src, [("Sarah\nJohnson", "NAME", 0)])
    once = _clip(src, [dict(e) for e in ents])
    twice = _clip(src, [dict(e) for e in once])
    return (once == twice, f"idempotent={once == twice}")
case("4c clip idempotent [must hold]", _e2e_idempotent)


def main():
    print("=" * 100)
    print("NAME-SPAN NEWLINE CLIP - span-layer evidence table")
    print("clip under test:", "present" if HAVE_CLIP else "MISSING (HEAD)")
    print("=" * 100)
    print(f"{'case':68s} {'status':6s} evidence")
    print("-" * 100)
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
        print(f"{name:68s} [{'PASS' if ok else 'FAIL'}] {ev}")
    print("-" * 100)
    print(f"{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
