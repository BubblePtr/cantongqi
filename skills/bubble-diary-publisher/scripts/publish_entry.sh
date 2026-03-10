#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="$SCRIPT_DIR/validate_entry.mjs"

REPO_PATH=""
ENTRY_PATH=""
ALLOW_OVERWRITE="false"
SKIP_PULL="false"

usage() {
  cat <<'EOF'
Usage:
  publish_entry.sh --entry <entry-json-path> [--repo <bubble-build-path>] [--allow-overwrite] [--skip-pull]

If --repo is omitted, the current working directory is used as the bubble-build repository.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO_PATH="${2:-}"
      shift 2
      ;;
    --entry)
      ENTRY_PATH="${2:-}"
      shift 2
      ;;
    --allow-overwrite)
      ALLOW_OVERWRITE="true"
      shift
      ;;
    --skip-pull)
      SKIP_PULL="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$ENTRY_PATH" ]]; then
  usage >&2
  exit 1
fi

if [[ -z "$REPO_PATH" ]]; then
  REPO_PATH="$(pwd)"
else
  REPO_PATH="$(cd "$REPO_PATH" && pwd)"
fi

ENTRY_PATH="$(cd "$(dirname "$ENTRY_PATH")" && pwd)/$(basename "$ENTRY_PATH")"

node "$VALIDATOR" "$ENTRY_PATH"

if ! git -C "$REPO_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $REPO_PATH" >&2
  exit 1
fi

if [[ -n "$(git -C "$REPO_PATH" status --short)" ]]; then
  echo "Repository has uncommitted changes: $REPO_PATH" >&2
  exit 1
fi

ENTRY_META="$(node --input-type=module -e '
  import fs from "fs";
  const entry = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  process.stdout.write(`${entry.date}\n${entry.entry_id}`);
' "$ENTRY_PATH")"

ENTRY_DATE="$(printf '%s\n' "$ENTRY_META" | sed -n '1p')"
ENTRY_ID="$(printf '%s\n' "$ENTRY_META" | sed -n '2p')"
ENTRY_YEAR="${ENTRY_DATE:0:4}"
TARGET_DIR="$REPO_PATH/entries/$ENTRY_YEAR"
TARGET_FILE="$TARGET_DIR/$ENTRY_DATE.json"

mkdir -p "$TARGET_DIR"

if [[ "$SKIP_PULL" != "true" ]]; then
  git -C "$REPO_PATH" pull --rebase
fi

EXISTED="false"
if [[ -f "$TARGET_FILE" ]]; then
  EXISTED="true"
  if [[ "$ALLOW_OVERWRITE" != "true" ]]; then
    echo "Target entry already exists: $TARGET_FILE" >&2
    exit 1
  fi
fi

cp "$ENTRY_PATH" "$TARGET_FILE"
git -C "$REPO_PATH" add "$TARGET_FILE"

if git -C "$REPO_PATH" diff --cached --quiet; then
  echo "No changes to commit for $ENTRY_ID"
  exit 0
fi

if [[ "$EXISTED" == "true" ]]; then
  COMMIT_MESSAGE="fix(entry): update bubble diary $ENTRY_DATE"
else
  COMMIT_MESSAGE="feat(entry): add bubble diary $ENTRY_DATE"
fi

git -C "$REPO_PATH" commit -m "$COMMIT_MESSAGE"
git -C "$REPO_PATH" push

COMMIT_HASH="$(git -C "$REPO_PATH" rev-parse HEAD)"
echo "Published $ENTRY_ID to $TARGET_FILE"
echo "Commit: $COMMIT_HASH"
