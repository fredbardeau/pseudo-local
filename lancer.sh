#!/bin/sh
# Ouvre l'interface de relecture dans le navigateur, hors ligne.
cd "$(dirname "$0")" || exit 1
exec uv run python -m pseudo.cli interface "$@"
