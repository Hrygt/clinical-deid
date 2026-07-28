"""Log-print PHI guard (fix/log-prints-offsets-only).

The name-fragment repair, newline-clip, and SAFE-veto paths emit diagnostic prints
to stdout -> journald. A print may carry span OFFSETS AND LENGTHS ONLY — never a
character of note text. Ruling 2026-07-27: journald is ephemeral (nightly rebuild)
but PHI in any log stream is a defect; diagnostics must stay useful via offsets.

Each case below drives one print path with a PLANTED name that cannot occur in
legitimate diagnostics (Zyxxlebot / Qwortham / Vlorpstein) and asserts:
  1. zero planted characters in captured stdout (the PHI guard), and
  2. the span offsets DO appear (the diagnostic stays useful).

Runs with hand-built entity sets, NO model / NO GPU.
"""
import io
import os
import sys
from contextlib import redirect_stdout

os.environ.setdefault("DEID_SKIP_MODEL_LOAD", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import (  # noqa: E402
    _repair_name_span_fragments,
    _clip_name_spans_at_line_breaks,
    filter_safe_spans,
)

PLANTED = ("Zyxxlebot", "Qwortham", "Vlorpstein", "yxxlebot", "wortham", "lorpstein")


def _run(fn, text, entities):
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(text, entities)
    return buf.getvalue()


def _assert_clean(case, out, *expected_offsets):
    for token in PLANTED:
        assert token.lower() not in out.lower(), (
            f"{case}: planted PHI {token!r} leaked into print output:\n{out}")
    for off in expected_offsets:
        assert off in out, (
            f"{case}: expected offset marker {off!r} missing — diagnostic lost:\n{out}")


def test_fragment_expand_print_carries_no_name_text():
    # span over a trailing fragment of the planted name -> expand path prints
    text = "Seen by Zyxxlebot today."
    s, en = text.index("yxxlebot"), text.index("yxxlebot") + len("yxxlebot")
    ents = [{"type": "LAST_NAME", "start": s, "end": en, "text": text[s:en]}]
    out = _run(_repair_name_span_fragments, text, ents)
    if "expand" in out:  # the path fired; its print must be offsets-only
        _assert_clean("fragment-expand", out, f"{s}:{en}")


def test_fragment_drop_print_carries_no_text():
    # fragment inside a whitelisted word -> drop path prints
    text = "Continue propranolol daily."
    s, en = text.index("pranolol"), text.index("pranolol") + len("pranolol")
    ents = [{"type": "LAST_NAME", "start": s, "end": en, "text": text[s:en]}]
    out = _run(_repair_name_span_fragments, text, ents)
    assert "drop" in out, "whitelist drop path did not fire — fixture broken"
    assert "pranolol" not in out.lower().replace("propranolol", ""), (
        f"fragment text leaked: {out}")
    _assert_clean("fragment-drop", out, f"{s}:{en}")


def test_fragment_merge_print_carries_no_name_text():
    # two fragments expanding to the same planted word -> merge path prints
    text = "Family met Vlorpstein at bedside."
    w = text.index("Vlorpstein")
    ents = [
        {"type": "FIRST_NAME", "start": w, "end": w + 5, "text": text[w:w + 5]},
        {"type": "LAST_NAME", "start": w + 5, "end": w + 10, "text": text[w + 5:w + 10]},
    ]
    out = _run(_repair_name_span_fragments, text, ents)
    assert "merge" in out, "merge path did not fire — fixture broken"
    _assert_clean("fragment-merge", out)


def test_newline_clip_prints_carry_no_name_text():
    # NAME span crossing a line break -> clip path prints span + pieces
    text = "Signed\nQwortham\nZyxxlebot\nPlan continues."
    s = text.index("Qwortham")
    en = text.index("Zyxxlebot") + len("Zyxxlebot")
    ents = [{"type": "NAME", "start": s, "end": en, "text": text[s:en]}]
    out = _run(_clip_name_spans_at_line_breaks, text, ents)
    assert "name-newline-clip" in out, "clip path did not fire — fixture broken"
    _assert_clean("newline-clip", out, f"{s}:{en}")


def test_newline_clip_whitelist_drop_print_carries_no_text():
    # one clipped piece is whitelisted -> clip-drop path prints
    text = "Dr\nQwortham\npropranolol\ncontinued."
    s = text.index("Qwortham")
    en = text.index("propranolol") + len("propranolol")
    ents = [{"type": "NAME", "start": s, "end": en, "text": text[s:en]}]
    out = _run(_clip_name_spans_at_line_breaks, text, ents)
    assert "name-newline-clip drop" in out, "clip-drop path did not fire — fixture broken"
    _assert_clean("newline-clip-drop", out)


def test_safe_veto_print_carries_no_span_text():
    # entity contained in a SAFE zone -> veto print names the RULE, never the text.
    # Firing shape borrowed from test_safe_span_veto note11: room_token contains span.
    text = "Patient's location: RM06"
    s = text.index("RM06")
    ents = [{"type": "POSTCODE", "start": s, "end": s + 4, "text": text[s:s + 4]}]
    out = _run(filter_safe_spans, text, ents)
    assert "SAFE-veto" in out, "SAFE-veto path did not fire — fixture broken"
    assert "RM06" not in out, f"vetoed span text leaked: {out}"
    _assert_clean("safe-veto", out, f"{s}:{s + 4}")


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"{name:55s} [PASS]")
        except AssertionError as e:
            failures += 1
            print(f"{name:55s} [FAIL] {str(e).splitlines()[0][:110]}")
    print("-" * 80)
    print(f"{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
