#!/bin/bash
# clinical-deid deploy — the SOLE deploy authority (RULING 2026-07-27).
#
# The pinned-SHA boot reconcile (reconcile.sh) is RETIRED; see docs/DEPLOY.md for the
# tombstone. The S3-sync substrate is now the only path by which code reaches the box, and
# this script is the only thing that writes to it.
#
# ATOMICITY CONTRACT — code + pin + VERSION move as ONE step.
#   S3 has no cross-object transaction, so "atomic" here means: a single staged payload is
#   built and fingerprinted BEFORE anything is uploaded, every object is derived from that
#   one payload, and the DEPLOY_MANIFEST — the object that makes a commit SHA believable —
#   is uploaded LAST. Any interruption therefore leaves the box in a state where the
#   manifest fingerprint does not match the running code, and /deid/health reports
#   version_verified=false. A partial deploy is LOUD, never silently mislabeled.
#   There is no rollback path: nothing on the box moves code except this script.
#
# Usage:
#   bash deploy_deid.sh --dry-run            # print the plan, mutate nothing
#   bash deploy_deid.sh                      # deploy current HEAD
#   bash deploy_deid.sh <commit-ish>         # deploy a specific commit
set -uo pipefail

S3_APP="s3://cpt-dnn-model-artifacts-675138611834/clinical-deid/app"
S3_PIN="s3://cpt-dnn-model-artifacts-675138611834/clinical-deid/deploy/TARGET_SHA"
INSTANCE_ID="${DEID_INSTANCE_ID:-i-00a456770a78d87cb}"
REGION="${AWS_REGION:-us-west-2}"
DEPLOY_DIR="/opt/clinical-deid"
HEALTH_URL="${DEID_HEALTH_URL:-https://deid.riggsmedai.com/deid/health}"
# The files the service actually runs. MUST stay in sync with
# code_fingerprint.SERVICE_MODULES — the fingerprint below is computed over exactly these.
SERVICE_FILES=(api.py deid.py medical_whitelist.py labels.py)

DRYRUN=0
TARGET="HEAD"
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRYRUN=1 ;;
    -*) echo "unknown flag: $arg" >&2; exit 2 ;;
    *) TARGET="$arg" ;;
  esac
done

log() { echo "[deploy] $*"; }
die() { echo "[deploy] ABORT: $*" >&2; exit 1; }

command -v aws >/dev/null || die "aws cli not found"
command -v git >/dev/null || die "git not found"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside the repo"
cd "$REPO_ROOT" || die "cannot cd to repo root"

SHA="$(git rev-parse --verify --quiet "${TARGET}^{commit}")" || die "cannot resolve '$TARGET'"

# --- Preflight: refuse to ship anything a reviewer cannot look up ------------------
if [ -n "$(git status --porcelain -- "${SERVICE_FILES[@]}")" ]; then
  die "service files are dirty in the working tree — commit or stash first"
fi
if ! git merge-base --is-ancestor "$SHA" origin/main 2>/dev/null; then
  if [ "${DEID_ALLOW_UNMERGED:-0}" != "1" ]; then
    die "$SHA is not an ancestor of origin/main (set DEID_ALLOW_UNMERGED=1 to override)"
  fi
  log "WARNING: $SHA is not on origin/main — proceeding under DEID_ALLOW_UNMERGED=1"
fi

PY="${DEID_PYTHON:-python}"
command -v "$PY" >/dev/null || PY="$REPO_ROOT/.venv/Scripts/python.exe"
[ -x "$PY" ] || command -v "$PY" >/dev/null || die "no python found for fingerprinting"

# --- Stage the payload ONCE; everything below derives from this one tree ------------
STAGE="$(mktemp -d)" || die "cannot create stage dir"
cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

git archive --format=tar "$SHA" | tar -x -C "$STAGE" || die "staging failed"
for f in "${SERVICE_FILES[@]}"; do
  [ -f "$STAGE/$f" ] || die "service file missing from commit $SHA: $f"
done

# Fingerprint the STAGED payload with the same module the service uses at runtime, so
# deploy-time and run-time can never drift apart.
FP="$("$PY" "$STAGE/code_fingerprint.py" "$STAGE" 2>/dev/null | tr -d '[:space:]')"
[ -n "$FP" ] || die "could not fingerprint the staged payload"

# VERSION and the manifest are written INTO the staged tree, so they ship in the same
# sync as the code they describe — this is the "one step" the ruling requires.
printf '%s\n' "$SHA" > "$STAGE/VERSION"
printf '{\n  "commit": "%s",\n  "fingerprint": "%s",\n  "deployed_by": "deploy_deid.sh"\n}\n' \
  "$SHA" "$FP" > "$STAGE/$(basename DEPLOY_MANIFEST.json)"

log "commit      : $SHA"
log "fingerprint : $FP"
log "payload     : ${SERVICE_FILES[*]} + VERSION + DEPLOY_MANIFEST.json"
log "s3 app      : $S3_APP"
log "s3 pin      : $S3_PIN"
log "instance    : $INSTANCE_ID ($REGION)"

if [ "$DRYRUN" = "1" ]; then
  log "DRY RUN — the single mutating step would be:"
  log "  1. aws s3 cp  <staged code + VERSION>  $S3_APP/    (code and VERSION together)"
  log "  2. aws s3 cp  <staged manifest>        $S3_APP/DEPLOY_MANIFEST.json  (LAST: makes the SHA believable)"
  log "  3. aws s3 cp  <sha>                    $S3_PIN     (bookkeeping record of what was shipped)"
  log "  4. ssm: s3 sync -> $DEPLOY_DIR, restart clinical-deid"
  log "  5. verify $HEALTH_URL reports version=$SHA AND version_verified=true AND fingerprint=$FP"
  log "DRY RUN — nothing was uploaded, nothing on the box was touched."
  exit 0
fi

# --- The one mutating step ----------------------------------------------------------
for f in "${SERVICE_FILES[@]}" VERSION; do
  aws s3 cp "$STAGE/$f" "$S3_APP/$f" --only-show-errors || die "upload failed: $f (payload incomplete; manifest NOT written, so health will report unverified)"
done
aws s3 cp "$STAGE/code_fingerprint.py" "$S3_APP/code_fingerprint.py" --only-show-errors \
  || die "upload failed: code_fingerprint.py"
# Manifest LAST — until it lands, the box cannot claim a verified SHA.
aws s3 cp "$STAGE/DEPLOY_MANIFEST.json" "$S3_APP/DEPLOY_MANIFEST.json" --only-show-errors \
  || die "upload failed: DEPLOY_MANIFEST.json"
printf '%s\n' "$SHA" | aws s3 cp - "$S3_PIN" --only-show-errors || die "pin write failed"
log "S3 substrate updated (code + VERSION + manifest + pin)"

CMD_ID="$(aws ssm send-command --instance-ids "$INSTANCE_ID" --region "$REGION" \
  --document-name AWS-RunShellScript \
  --parameters "commands=[\"aws s3 sync $S3_APP/ $DEPLOY_DIR/ --exact-timestamps\",\"systemctl restart clinical-deid\",\"sleep 45\",\"systemctl is-active clinical-deid\"]" \
  --query 'Command.CommandId' --output text)" || die "ssm send-command failed"
log "ssm command: $CMD_ID (waiting)"
for _ in $(seq 1 40); do
  STATUS="$(aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
    --region "$REGION" --query 'Status' --output text 2>/dev/null)"
  case "$STATUS" in
    Success) break ;;
    Failed|Cancelled|TimedOut) die "ssm command $STATUS" ;;
  esac
  sleep 10
done
[ "$STATUS" = "Success" ] || die "ssm command did not reach Success (last: ${STATUS:-none})"

# --- Verify the RUNNING code, not a file ---------------------------------------------
HEALTH="$(curl -s --max-time 30 "$HEALTH_URL")" || die "health check unreachable"
echo "$HEALTH" | grep -q "\"version\":\"$SHA\"" || die "health version != $SHA -> $HEALTH"
echo "$HEALTH" | grep -q '"version_verified":true' || die "health version NOT verified -> $HEALTH"
echo "$HEALTH" | grep -q "\"code_fingerprint\":\"$FP\"" || die "running fingerprint != staged -> $HEALTH"
log "VERIFIED: running code is $SHA (fingerprint $FP)"
log "An immediate relaunch is safe: bootstrap syncs the same S3 payload, which is this commit."
