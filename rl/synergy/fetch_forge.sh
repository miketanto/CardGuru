#!/usr/bin/env bash
# Fetch Forge card scripts + editions at the release that shipped FRA.
# Scryfall (api.scryfall.com) is denied by this container's network
# policy; github.com over git is allowed, so Forge is the data source.
set -euo pipefail
TAG=${TAG:-forge-2.0.15}
DEST=${DEST:-/home/user/forge}
mkdir -p "$DEST" && cd "$DEST"
[ -d .git ] || git clone -q --filter=blob:none --no-checkout --depth 1 --branch "$TAG" \
  https://github.com/Card-Forge/forge.git .
git sparse-checkout set --no-cone 'forge-gui/res/editions/*' 'forge-gui/res/cardsfolder/**' 'forge-gui/res/tokenscripts/*'
git checkout -q "$TAG"
HERE=$(dirname "$(readlink -f "$0")")
cd "$HERE"
python3 fra_cardlist.py "$DEST/forge-gui/res/editions/Reality Fracture.txt" fra_cards.json
python3 forge_parse.py "$DEST/forge-gui/res/cardsfolder" fra_cards.json fra_parsed.json
python3 tally.py fra_parsed.json TALLIES.md tallies.json > /dev/null
python3 signals.py fra_parsed.json "$DEST/forge-gui/res/tokenscripts" fra_signals.json > /dev/null
