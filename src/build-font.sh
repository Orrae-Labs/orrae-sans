#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
type_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

if [[ -n "${FONTTOOLS_PYTHON:-}" ]]; then
  fonttools_python=$FONTTOOLS_PYTHON
elif command -v brew >/dev/null 2>&1 && [[ -x "$(brew --prefix fonttools)/libexec/bin/python" ]]; then
  fonttools_python="$(brew --prefix fonttools)/libexec/bin/python"
else
  fonttools_python=${PYTHON:-python3}
fi

fontforge_bin=${FONTFORGE_BIN:-$(command -v fontforge)}
woff2_bin=${WOFF2_BIN:-$(command -v woff2_compress)}

mkdir -p "$type_root/build" "$type_root/dist"

"$fonttools_python" "$type_root/src/build_font.py" "$type_root/build/OrraeSans-Raw.ttf"
"$fontforge_bin" -script "$type_root/src/clean_font.py" \
  "$type_root/build/OrraeSans-Raw.ttf" \
  "$type_root/dist/OrraeSans-Regular.ttf" \
  "$type_root/dist/OrraeSans-Regular.otf"

"$fonttools_python" "$type_root/src/normalize_font.py" \
  "$type_root/dist/OrraeSans-Regular.ttf" \
  "$type_root/dist/OrraeSans-Regular.otf"

cp "$type_root/dist/OrraeSans-Regular.ttf" "$type_root/dist/OrraeSans-Regular-web.ttf"
"$woff2_bin" "$type_root/dist/OrraeSans-Regular-web.ttf"
mv "$type_root/dist/OrraeSans-Regular-web.woff2" "$type_root/dist/OrraeSans-Regular.woff2"
rm "$type_root/dist/OrraeSans-Regular-web.ttf"

"$fonttools_python" -m fontTools.ttx -l "$type_root/dist/OrraeSans-Regular.ttf"
"$fonttools_python" -m fontTools.ttx -l "$type_root/dist/OrraeSans-Regular.otf"
"$fonttools_python" -m fontTools.ttx -l "$type_root/dist/OrraeSans-Regular.woff2"
fontlint "$type_root/dist/OrraeSans-Regular.ttf"
fontlint "$type_root/dist/OrraeSans-Regular.otf"
hb-shape "$type_root/dist/OrraeSans-Regular.ttf" 'HAMBURGEFONS 0123456789'
hb-shape --features=ss01 "$type_root/dist/OrraeSans-Regular.ttf" 'A'

(
  cd "$type_root/dist"
  shasum -a 256 OrraeSans-Regular.ttf OrraeSans-Regular.otf \
    OrraeSans-Regular.woff2 > SHA256SUMS
  shasum -a 256 -c SHA256SUMS
)
