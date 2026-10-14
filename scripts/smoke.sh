#!/usr/bin/env bash
# End-to-end smoke test against a running stack (docker compose up): upload, ask, check citations.
#   scripts/smoke.sh [base_url]
set -euo pipefail

BASE="${1:-http://localhost:8080}"
API="$BASE/api/v1"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
# Git Bash on Windows hands native curl a path it cannot read; harmless elsewhere.
if command -v cygpath >/dev/null 2>&1; then HERE="$(cygpath -m "$HERE")"; fi

fail() { echo "FAIL: $*" >&2; exit 1; }

echo "meta"
curl -fsS "$API/meta" | grep -q '"streaming_chat":true' || fail "streaming not advertised"

echo "upload"
upload=$(curl -fsS -F "file=@$HERE/samples/employee-handbook-en.pdf;type=application/pdf" "$API/documents/upload")
echo "$upload" | grep -q '"status":"READY"' || fail "document not ready: $upload"
doc=$(echo "$upload" | sed -E 's/.*"document_id":"([^"]+)".*/\1/')

echo "ask (english)"
answer=$(curl -fsS -H 'Content-Type: application/json' \
  -d "{\"document_id\":\"$doc\",\"message\":\"How many vacation days do I get?\"}" "$API/chats/chat")
echo "$answer" | grep -q 'twenty days' || fail "wrong answer: $answer"
echo "$answer" | grep -q '"page":2' || fail "missing page citation: $answer"

echo "ask (stream)"
stream=$(curl -fsSN -H 'Content-Type: application/json' \
  -d "{\"document_id\":\"$doc\",\"message\":\"How many vacation days do I get?\"}" "$API/chats/chat/stream")
echo "$stream" | grep -q '^event: done' || fail "stream did not finish: $stream"

echo "ask (spanish document)"
es=$(curl -fsS -F "file=@$HERE/samples/manual-del-empleado-es.pdf;type=application/pdf" "$API/documents/upload")
esdoc=$(echo "$es" | sed -E 's/.*"document_id":"([^"]+)".*/\1/')
# The body goes through a file so accented characters reach the API byte for byte on any OS.
body="$(mktemp)"
printf '{"document_id":"%s","message":"¿Cuántos días de vacaciones tengo?"}' "$esdoc" > "$body"
if command -v cygpath >/dev/null 2>&1; then body_arg="$(cygpath -m "$body")"; else body_arg="$body"; fi
reply=$(curl -fsS -H 'Content-Type: application/json; charset=utf-8' --data-binary "@$body_arg" "$API/chats/chat")
rm -f "$body"
echo "$reply" | grep -q 'veinte' || fail "wrong Spanish answer: $reply"

echo "cleanup"
curl -fsS -X DELETE "$API/documents/$doc" >/dev/null
curl -fsS -X DELETE "$API/documents/$esdoc" >/dev/null
echo "OK"
