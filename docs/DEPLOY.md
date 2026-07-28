# clinical-deid deploy

**The S3-sync substrate is the sole deploy authority.** One script writes to it:
`deploy_deid.sh`. Nothing else moves code onto the box.

```bash
bash deploy_deid.sh --dry-run      # print the plan, mutate nothing
bash deploy_deid.sh                # deploy current HEAD
bash deploy_deid.sh <commit-ish>   # deploy a specific commit
```

## How code reaches the box

`launch template v9` → user-data → `s3://cpt-dnn-model-artifacts-675138611834/deploy/bootstrap.sh`
→ `aws s3 sync s3://.../clinical-deid/app/ /opt/clinical-deid/` → `clinical-deid.service`.

Boot and redeploy therefore take the **same** path: whatever is in the S3 `app/` prefix is
what runs. There is no second mechanism, no overlay, and **no rollback path** — a relaunch
cannot land on anything other than the payload the last deploy uploaded.

## Atomicity contract

S3 has no cross-object transaction, so "atomic" is enforced by construction rather than by
the API:

1. One payload is staged from a single commit (`git archive`) and fingerprinted **before**
   anything is uploaded. Every uploaded object derives from that one tree.
2. `VERSION` and `DEPLOY_MANIFEST.json` are written **into the staged tree**, so they ship
   in the same operation as the code they describe.
3. The manifest — the only thing that makes a commit SHA believable — is uploaded **last**.

An interrupted deploy therefore leaves a box whose manifest fingerprint does not match its
running code, and `/deid/health` reports `version_verified: false`. **A partial deploy is
loud, never silently mislabeled.**

## /deid/health reports the RUNNING code

```json
{"version": "<commit sha>", "version_verified": true, "code_fingerprint": "<sha256>"}
```

`code_fingerprint` is computed from the bytes of the files backing the **loaded modules**
(`code_fingerprint.fingerprint_running`), so it is derived from the running artifact by
construction. The commit SHA is reported only when the deploy manifest's recorded
fingerprint equals it. Otherwise the endpoint returns `version_verified: false` and an
explicit reason (`unverified:no-manifest`, `unverified:fingerprint-mismatch`,
`unverified:no-fingerprint`) rather than a SHA that would be a lie.

Deploy-time and run-time fingerprints both go through `code_fingerprint.py`, over the same
named file set (`SERVICE_MODULES`), so they cannot drift apart. **If you add a module the
service imports, add it to `SERVICE_MODULES` and to `SERVICE_FILES` in `deploy_deid.sh` in
the same commit** — the engine repo has been bitten four times by a deploy file list that
lagged an import.

---

## TOMBSTONE — the pinned-SHA boot reconcile (retired 2026-07-27)

`reconcile.sh` and `clinical-deid-reconcile.service` are **removed**. Do not reintroduce
them, and do not "fix" the S3 pin by giving it a consumer again.

**What it was.** A boot-time oneshot that read a pinned SHA from
`s3://.../clinical-deid/deploy/TARGET_SHA`, cloned the GitHub repo, asserted the pin
resolved, and overlaid the tracked tree onto `/opt/clinical-deid`. Its stated purpose was
to stop prod drifting to unreviewed `main`.

**Why it is gone.**

- **It was never installed on prod.** The live `bootstrap.sh` uses the S3-sync substrate and
  never wrote the systemd unit; the unit existed only in `user-data-both.sh`, which the
  launch template does not use. Verified 2026-07-27: `clinical-deid-reconcile.service`
  could not be found on the running instance. The script was dead code, and the pin it read
  was advisory — a number nobody enforced.
- **Two authorities, one of them fictional, is worse than one.** The pin sat at `4a3889e1`
  while the box ran `97b6d726`. Had the unit ever been installed, a relaunch would have
  rolled prod **backwards past the 2026-07-19 newline fix**. A rollback path that exists
  only in a file nobody executes is a trap for the next reader, not a safeguard.
- **It fetched from GitHub at boot**, adding a network dependency and a second source of
  truth alongside S3.

**What replaces each property:**

| reconcile.sh property | replacement |
|---|---|
| prod cannot drift to unreviewed `main` | `deploy_deid.sh` refuses a commit that is not an ancestor of `origin/main` (explicit `DEID_ALLOW_UNMERGED=1` override, logged) |
| a human decides when prod moves | unchanged — nothing moves code except a human running `deploy_deid.sh` |
| deployed SHA is visible | `/deid/health`, now derived from the running artifact instead of a file that could go stale |
| self-heal on relaunch | the substrate *is* the source of truth; a relaunch syncs it, so there is nothing to heal |

`TARGET_SHA` still exists and is still written by every deploy, as a **bookkeeping record of
what was last shipped**. Nothing reads it to make a decision.

---

## Retroactive repair: the 24-hour window

**Stored de-identified text cannot be regenerated after a de-id fix.** Raw source text is
retained nowhere durable: the accuracy store keeps `note_sha256` + `deid_note` only, the
grader report store never receives raw text, and the gold corpus holds de-identified text
built from already-de-identified sources.

The **only** retroactive repair that will ever exist is `accuracy-originals`, which holds
raw note text under a **24-hour TTL** and is hard-deleted at the first PHI render. A batch
graded within the last 24 hours and never PHI-rendered can be re-de-identified; everything
older is **permanently** carrying whatever de-id artifacts were present when it was stored.

Consequence to state plainly when reporting any de-id fix: fixes are **forward-only**. They
change the evidence trail from the deploy onward and repair nothing already stored. (The
accuracy reporters replay stored grades rather than regrading, so no number a physician has
already seen changes either way — but three portal-side layers do recompute over stored
de-identified text at render time: the clone gate, the time-scope exit, and the Cat 2/3
wording refinement.)
