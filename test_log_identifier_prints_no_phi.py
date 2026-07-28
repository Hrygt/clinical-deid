"""Identifier-repair log-print PHI guard (fix/log-identifier-repair-offsets).

Sibling of fix/log-prints-offsets-only (the name-print class, shipped 2026.07.27):
the _repair_identifier_spans prints leaked span text — `run='<8 digits>'` puts an
MRN-shaped digit run straight into journald, and the drop/trim/geo prints leak the
span characters. Live-witnessed on the deid box journal during the 2026-07-27
post-deploy check. Every repair print goes offsets-and-lengths-only.

Each case drives one print path with a PLANTED MRN-like run (84719362) or word and
asserts: (1) zero planted characters in captured stdout, (2) offsets survive.
Runs with hand-built entity sets, NO model / NO GPU.
"""
import io
import os
import sys
from contextlib import redirect_stdout

os.environ.setdefault("DEID_SKIP_MODEL_LOAD", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deid import _repair_identifier_spans  # noqa: E402

PLANTED = ("84719362", "4719362", "KETHLEY", "ESOPHAGOGASTRO")


def _run(text, entities):
    buf = io.StringIO()
    with redirect_stdout(buf):
        _repair_identifier_spans(entities, text)
    return buf.getvalue()


def _assert_clean(case, out, *expected_offsets):
    for token in PLANTED:
        assert token.lower() not in out.lower(), (
            f"{case}: planted text {token!r} leaked into print output:\n{out}")
    for off in expected_offsets:
        assert off in out, f"{case}: offset marker {off!r} missing — diagnostic lost:\n{out}"


def _ent(t, s, e, text):
    return [{"type": t, "start": s, "end": e, "text": text[s:e]}]


def test_id_span_drop_no_digit():
    text = "Procedure: ESOPHAGOGASTRODUODENOSCOPY done."
    s = text.index("ESOPHAGOGASTRO")
    out = _run(text, _ent("UNIQUE_ID", s, s + 14, text))
    assert "id-span drop" in out, "drop path did not fire — fixture broken"
    _assert_clean("id-span-drop", out, f"{s}:{s + 14}")


def test_id_span_over_match_trim():
    text = "MRN 84719362ABC continues."
    s = text.index("84719362")
    # span edge sits INSIDE the trailing alpha run ('C' follows) -> trim fires
    out = _run(text, _ent("MEDICAL_RECORD_NUMBER", s, s + 10, text))
    assert "over-match trim" in out, "trim path did not fire — fixture broken"
    _assert_clean("id-span-trim", out, f"{s}:{s + 10}")


def test_sub_run_drop_long_run():
    # span is a proper sub-run of the planted 8-digit MRN — the run='…' leak site
    text = "ID 84719362 recorded."
    s = text.index("4719362")
    out = _run(text, _ent("MEDICAL_RECORD_NUMBER", s, s + 7, text))
    assert "sub-run drop" in out, "sub-run drop path did not fire — fixture broken"
    _assert_clean("sub-run-drop", out, f"{s}:{s + 7}")


def test_sub_run_expand_short_run():
    text = "Room 4102 today."
    s = text.index("102")
    out = _run(text, _ent("UNIQUE_ID", s, s + 3, text))
    assert "sub-run expand" in out, "expand path did not fire — fixture broken"
    assert "4102" not in out, f"expanded run text leaked: {out}"
    _assert_clean("sub-run-expand", out)


def test_geo_span_complete():
    text = "Lives at 3214 KETHLEY Road."
    s = text.index("3214")
    e = text.index("KETH") + 4  # edge mid-word
    out = _run(text, _ent("STREET_ADDRESS", s, e, text))
    assert "geo-span complete" in out, "geo path did not fire — fixture broken"
    _assert_clean("geo-span-complete", out)


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"{name:45s} [PASS]")
        except AssertionError as e:
            failures += 1
            print(f"{name:45s} [FAIL] {str(e).splitlines()[0][:110]}")
    print("-" * 78)
    print(f"{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
