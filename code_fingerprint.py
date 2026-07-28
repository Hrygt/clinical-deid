"""Running-code fingerprint — the single source of truth for "what code is this
process actually executing?" (RULING 2026-07-27: /deid/health must report the RUNNING
code SHA, never a file that can go stale).

The old contract read /opt/clinical-deid/VERSION and reported whatever string it found.
That file is written by the deploy and is not coupled to the code in any way, so it
could — and on 2026-07-27 did — report a SHA two commits behind the code actually
running. A version endpoint that can lie is worse than no version endpoint.

New contract, in two parts:

  1. `fingerprint_running()` hashes the BYTES OF THE FILES BACKING THE LOADED MODULES
     (via each module's __file__). It is derived from the running artifact by
     construction — there is no file it could read that would let it disagree with the
     code in memory.

  2. The deploy writes DEPLOY_MANIFEST.json recording {commit, fingerprint} for the tree
     it shipped. /deid/health reports the commit SHA as VERIFIED only when the manifest's
     fingerprint equals the fingerprint computed from the running modules. Any
     divergence — hand-patched file, half-finished sync, stale VERSION — reports
     version_verified=false and the raw fingerprint instead of a SHA that would be a lie.

Deploy-time and run-time must agree exactly, so both go through this module:
`fingerprint_dir()` (deploy, over a staged tree) and `fingerprint_running()` (service).
Both hash the SAME NAMED FILE SET, so the two cannot drift apart silently.

Byte-exactness note: files in this repo are stored and checked out CRLF, and the S3
substrate copies bytes verbatim, so the staged-tree fingerprint equals the on-box
fingerprint. Nothing here normalizes line endings — normalizing would hide exactly the
kind of substitution this is meant to detect.
"""
import hashlib
import json
import os
import sys

# The modules that constitute the running service. Anything whose behavior can change a
# de-identification result belongs here. (Test files and training scripts do not — they
# are never imported by the service.)
SERVICE_MODULES = ("api", "deid", "medical_whitelist", "labels")

MANIFEST_NAME = "DEPLOY_MANIFEST.json"


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _combine(pairs) -> str:
    """Fold (name, filehash) pairs into one fingerprint. Sorted by name, and the name is
    hashed alongside the content so a rename cannot preserve the fingerprint."""
    h = hashlib.sha256()
    for name, digest in sorted(pairs):
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update(digest.encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def fingerprint_dir(directory: str, modules=SERVICE_MODULES) -> str:
    """Fingerprint a STAGED tree (deploy side). Every service module must be present —
    a missing file is a broken payload and raises rather than hashing a partial tree."""
    pairs = []
    for mod in modules:
        path = os.path.join(directory, f"{mod}.py")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"service module missing from payload: {path}")
        pairs.append((f"{mod}.py", _sha256_file(path)))
    return _combine(pairs)


def fingerprint_running(modules=SERVICE_MODULES) -> str:
    """Fingerprint the RUNNING artifact (service side): hash the file backing each loaded
    module. Returns "" if any service module is not loaded or has no readable file — the
    caller must then treat the version as unverified rather than guessing."""
    pairs = []
    for mod in modules:
        m = sys.modules.get(mod)
        path = getattr(m, "__file__", None) if m is not None else None
        if not path or not os.path.isfile(path):
            return ""
        try:
            pairs.append((f"{mod}.py", _sha256_file(path)))
        except OSError:
            return ""
    return _combine(pairs)


def read_manifest(directory: str) -> dict:
    """Read DEPLOY_MANIFEST.json from a deploy directory. Never raises."""
    try:
        with open(os.path.join(directory, MANIFEST_NAME)) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def resolve_version(deploy_dir: str, modules=SERVICE_MODULES) -> dict:
    """Resolve what /deid/health should report.

    Returns {version, version_verified, code_fingerprint}:
      * fingerprint computed from the RUNNING modules (never from a file on disk);
      * version = the manifest commit ONLY when the manifest fingerprint matches it;
      * otherwise version_verified=False and version carries an explicit reason, so a
        stale or hand-patched box is visible at the endpoint instead of silently
        reporting a SHA that does not describe the running code.
    Never raises — /deid/health must not be breakable by version bookkeeping."""
    try:
        running = fingerprint_running(modules)
    except Exception:  # noqa: BLE001
        running = ""
    if not running:
        return {"version": "unverified:no-fingerprint", "version_verified": False,
                "code_fingerprint": ""}

    manifest = read_manifest(deploy_dir)
    commit = str(manifest.get("commit") or "")
    recorded = str(manifest.get("fingerprint") or "")
    if not commit or not recorded:
        return {"version": "unverified:no-manifest", "version_verified": False,
                "code_fingerprint": running}
    if recorded != running:
        return {"version": "unverified:fingerprint-mismatch", "version_verified": False,
                "code_fingerprint": running}
    return {"version": commit, "version_verified": True, "code_fingerprint": running}


if __name__ == "__main__":
    # Deploy-side CLI: print the fingerprint of a staged tree (default: this directory).
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    print(fingerprint_dir(target))
