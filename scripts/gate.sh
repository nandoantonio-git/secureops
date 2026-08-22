#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."

if [ "$#" -eq 0 ]; then
  echo "-> py_compile (todo o projeto)..."
  TARGETS=$(find secureops -name "*.py" 2>/dev/null)
else
  TARGETS=""
  for f in "$@"; do
    case "$f" in
      *.py) TARGETS="$TARGETS $f" ;;
      *) echo "-> pulando (não é .py): $f" ;;
    esac
  done
fi

TARGETS="$(echo "$TARGETS" | xargs)"

if [ -z "$TARGETS" ]; then
  echo "OK: gate passou (nenhum .py para checar)"
  exit 0
fi

echo "-> py_compile: $TARGETS"
if ! python3 -m py_compile $TARGETS; then
  echo "FAIL: gate falhou (py_compile)"
  exit 1
fi

if command -v ruff >/dev/null 2>&1; then
  echo "-> ruff check..."
  if ! ruff check $TARGETS; then
    echo "FAIL: gate falhou (ruff)"
    exit 1
  fi
fi

echo "OK: gate passou"
exit 0
