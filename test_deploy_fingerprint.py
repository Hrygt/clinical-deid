"""Running-code fingerprint / version-honesty tests (chore/retire-reconcile,
RULING 2026-07-27: /deid/health must report the RUNNING code SHA, never a file that
can go stale).

The defect this closes was witnessed on 2026-07-27: /deid/health reported
4a3889e1 while the box was running 97b6d726, because the endpoint echoed whatever
string sat in /opt/clinical-deid/VERSION. The new contract makes the reported SHA
a CLAIM THAT CAN FAIL: it is believed only when the deploy manifest's recorded
fingerprint equals the fingerprint computed from the running modules.

The load-bearing property under test is NEGATIVE — no arrangement of files on disk
may produce version_verified=true for code that is not what the manifest describes.
Section 2 is therefore the real suite; section 1 is the happy path.

No model / no GPU (DEID_SKIP_MODEL_LOAD).

Run:  python test_deploy_fingerprint.py
"""
import json
import os
import shutil
import sys
import tempfile

os.environ.setdefault("DEID_SKIP_MODEL_LOAD", "1")

import code_fingerprint as cf  # noqa: E402

CASES = []


def case(name, fn):
    CASES.append((name, fn))


REPO = os.path.dirname(os.path.abspath(__file__))


def _stage(tmp, mutate=None, manifest="match", modules=cf.SERVICE_MODULES):
    """Build a fake deploy tree. mutate: (filename, extra_bytes) appended after the
    fingerprint would have been taken at deploy time. manifest: match|stale|absent|absent-commit."""
    d = os.path.join(tmp, "deploy")
    os.makedirs(d, exist_ok=True)
    for mod in modules:
        shutil.copy(os.path.join(REPO, f"{mod}.py"), os.path.join(d, f"{mod}.py"))
    fp_at_deploy = cf.fingerprint_dir(d, modules)
    if mutate:
        fname, extra = mutate
        with open(os.path.join(d, fname), "ab") as f:
            f.write(extra)
    if manifest == "match":
        body = {"commit": "deadbeef" * 5, "fingerprint": fp_at_deploy}
    elif manifest == "stale":
        body = {"commit": "deadbeef" * 5, "fingerprint": "0" * 64}
    elif manifest == "absent-commit":
        body = {"fingerprint": fp_at_deploy}
    else:
        body = None
    if body is not None:
        with open(os.path.join(d, cf.MANIFEST_NAME), "w") as f:
            json.dump(body, f)
    return d, fp_at_deploy


class _FakeMod:
    def __init__(self, path):
        self.__file__ = path


def _resolve_as_if_running(deploy_dir, modules=cf.SERVICE_MODULES):
    """Resolve version with sys.modules pointed at the staged tree — i.e. as if the
    service were running THAT code."""
    saved = {m: sys.modules.get(m) for m in modules}
    try:
        for m in modules:
            sys.modules[m] = _FakeMod(os.path.join(deploy_dir, f"{m}.py"))
        return cf.resolve_version(deploy_dir, modules)
    finally:
        for m, old in saved.items():
            if old is None:
                sys.modules.pop(m, None)
            else:
                sys.modules[m] = old


# ---- 1. Happy path ----
def _clean_deploy():
    with tempfile.TemporaryDirectory() as tmp:
        d, fp = _stage(tmp)
        info = _resolve_as_if_running(d)
        ok = (info["version_verified"] is True and info["version"] == "deadbeef" * 5
              and info["code_fingerprint"] == fp)
        return ok, f"verified={info['version_verified']} version={info['version'][:12]}..."
case("1a clean deploy reports the commit, verified [must verify]", _clean_deploy)


def _fingerprint_deterministic():
    with tempfile.TemporaryDirectory() as tmp:
        d, fp = _stage(tmp)
        return (cf.fingerprint_dir(d) == fp, f"stable={cf.fingerprint_dir(d) == fp}")
case("1b fingerprint is deterministic over the same tree [must hold]", _fingerprint_deterministic)


def _deploy_equals_running():
    # The whole design rests on these two agreeing; they hash the same named file set.
    with tempfile.TemporaryDirectory() as tmp:
        d, fp = _stage(tmp)
        info = _resolve_as_if_running(d)
        return (info["code_fingerprint"] == fp,
                f"deploy={fp[:16]} running={info['code_fingerprint'][:16]}")
case("1c deploy-time and run-time fingerprints agree [must match]", _deploy_equals_running)


# ---- 2. The negative property: a stale/patched box can never claim verified ----
def _patched_file():
    # A hand-patched module after deploy — the exact shape of the .bak-dated files
    # found on the box on 2026-07-27.
    with tempfile.TemporaryDirectory() as tmp:
        d, _ = _stage(tmp, mutate=("medical_whitelist.py", b"\n# hand patch\n"))
        info = _resolve_as_if_running(d)
        ok = info["version_verified"] is False and info["version"] == "unverified:fingerprint-mismatch"
        return ok, f"verified={info['version_verified']} version={info['version']}"
case("2a hand-patched module -> UNVERIFIED [must not verify]", _patched_file)


def _stale_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        d, _ = _stage(tmp, manifest="stale")
        info = _resolve_as_if_running(d)
        ok = info["version_verified"] is False
        return ok, f"verified={info['version_verified']} version={info['version']}"
case("2b manifest describing other code -> UNVERIFIED [must not verify]", _stale_manifest)


def _no_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        d, _ = _stage(tmp, manifest="absent")
        info = _resolve_as_if_running(d)
        ok = info["version_verified"] is False and info["version"] == "unverified:no-manifest"
        return ok, f"version={info['version']}"
case("2c no manifest (interrupted deploy) -> UNVERIFIED [must not verify]", _no_manifest)


def _manifest_without_commit():
    with tempfile.TemporaryDirectory() as tmp:
        d, _ = _stage(tmp, manifest="absent-commit")
        info = _resolve_as_if_running(d)
        return (info["version_verified"] is False, f"version={info['version']}")
case("2d manifest without a commit -> UNVERIFIED [must not verify]", _manifest_without_commit)


def _version_file_cannot_lie():
    # THE WITNESSED DEFECT: a VERSION file naming a different commit must have no
    # power to make the endpoint report that commit.
    with tempfile.TemporaryDirectory() as tmp:
        d, _ = _stage(tmp, manifest="absent")
        with open(os.path.join(d, "VERSION"), "w") as f:
            f.write("4a3889e139e684f1ed655271c65bdccbbbc4db89\n")
        info = _resolve_as_if_running(d)
        ok = info["version_verified"] is False and "4a3889e1" not in info["version"]
        return ok, f"version={info['version']} (stale VERSION ignored)"
case("2e stale VERSION file alone cannot produce a SHA [the 07-27 defect]",
     _version_file_cannot_lie)


def _module_not_loaded():
    with tempfile.TemporaryDirectory() as tmp:
        d, _ = _stage(tmp)
        saved = sys.modules.get("deid")
        try:
            sys.modules.pop("deid", None)
            info = cf.resolve_version(d)
            ok = info["version_verified"] is False
            return ok, f"version={info['version']}"
        finally:
            if saved is not None:
                sys.modules["deid"] = saved
case("2f a service module not loaded -> UNVERIFIED [must not verify]", _module_not_loaded)


def _rename_changes_fingerprint():
    with tempfile.TemporaryDirectory() as tmp:
        d, fp = _stage(tmp)
        # Swap two modules' contents: same bytes present, different names.
        a, b = os.path.join(d, "labels.py"), os.path.join(d, "medical_whitelist.py")
        ca, cb = open(a, "rb").read(), open(b, "rb").read()
        open(a, "wb").write(cb)
        open(b, "wb").write(ca)
        return (cf.fingerprint_dir(d) != fp, "swapped content changes fingerprint")
case("2g content swap between modules changes the fingerprint [must differ]",
     _rename_changes_fingerprint)


def _missing_file_raises():
    with tempfile.TemporaryDirectory() as tmp:
        d, _ = _stage(tmp)
        os.remove(os.path.join(d, "labels.py"))
        try:
            cf.fingerprint_dir(d)
            return (False, "fingerprint_dir accepted a partial payload")
        except FileNotFoundError:
            return (True, "partial payload raises at deploy time")
case("2h deploy-side: partial payload raises, never hashes a subset [must raise]",
     _missing_file_raises)


# ---- 3. Health endpoint never breakable by version bookkeeping ----
def _resolver_never_raises():
    bad = [os.path.join(REPO, "no-such-dir-xyz"), "", "/"]
    out = []
    for d in bad:
        try:
            info = cf.resolve_version(d)
            out.append(info["version_verified"])
        except Exception as exc:  # noqa: BLE001
            return (False, f"raised on {d!r}: {exc}")
    return (not any(out), f"verified flags for bad dirs = {out} [must all be False]")
case("3a resolver never raises and never verifies on a bad dir [must hold]",
     _resolver_never_raises)


def _api_exposes_fields():
    import api
    fields = api.HealthResponse.model_fields
    need = {"version", "version_verified", "code_fingerprint"}
    missing = need - set(fields)
    return (not missing, f"missing health fields={missing} [must stay empty]")
case("3b /deid/health response carries version_verified + code_fingerprint",
     _api_exposes_fields)


def _api_lazy_resolution():
    import api
    info = api.get_version_info()
    ok = set(info) == {"version", "version_verified", "code_fingerprint"}
    # In a repo checkout there is no manifest, so it MUST report unverified — and the
    # fingerprint must still be computable (api/deid/etc. are genuinely loaded here).
    ok = ok and info["version_verified"] is False and len(info["code_fingerprint"]) == 64
    return ok, f"version={info['version']} fp={info['code_fingerprint'][:16]}..."
case("3c live api.get_version_info: unverified in a checkout, fingerprint present",
     _api_lazy_resolution)


# ---- 4. Retirement is complete ----
def _reconcile_gone():
    present = os.path.exists(os.path.join(REPO, "reconcile.sh"))
    return (not present, f"reconcile.sh present={present} [must be False]")
case("4a reconcile.sh removed from the repo [must be gone]", _reconcile_gone)


def _deploy_script_present():
    p = os.path.join(REPO, "deploy_deid.sh")
    if not os.path.exists(p):
        return (False, "deploy_deid.sh missing")
    body = open(p, encoding="utf-8", errors="replace").read()
    # The file list the deploy ships must cover every module the fingerprint covers,
    # or a deploy could ship a tree the service then fails to verify.
    missing = [m for m in cf.SERVICE_MODULES if f"{m}.py" not in body]
    return (not missing, f"SERVICE_MODULES not in deploy file list={missing} [must stay empty]")
case("4b deploy script ships every fingerprinted module [must stay empty]",
     _deploy_script_present)


def _no_reconcile_references():
    stale = []
    for fn in os.listdir(REPO):
        if not fn.endswith((".py", ".sh")) or fn == "test_deploy_fingerprint.py":
            continue
        try:
            body = open(os.path.join(REPO, fn), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        # Only EXECUTABLE references count. A comment naming the retired script (the
        # tombstone pointer in deploy_deid.sh) is documentation, not a live consumer.
        code = "\n".join(ln for ln in body.splitlines() if not ln.lstrip().startswith("#"))
        if "reconcile.sh" in code or "clinical-deid-reconcile" in code:
            stale.append(fn)
    # user-data-both.sh is the historical launch script, superseded by the S3 bootstrap;
    # it is allowed to keep its reference only if it is not the live boot path.
    stale = [s for s in stale if s != "user-data-both.sh"]
    return (not stale, f"files still referencing reconcile={stale} [must stay empty]")
case("4c no live code references the retired reconcile [must stay empty]",
     _no_reconcile_references)


def main():
    print("=" * 104)
    print("DEPLOY FINGERPRINT / VERSION HONESTY - evidence table")
    print("=" * 104)
    print(f"{'case':72s} {'status':6s} evidence")
    print("-" * 104)
    failures = 0
    for name, fn in CASES:
        try:
            ok, ev = fn()
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
