#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
type_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

fonttools_python=${FONTTOOLS_PYTHON:-${PYTHON:-python3}}
fontmake_bin=${FONTMAKE_BIN:-$(command -v fontmake)}
canonical_ufo="$type_root/sources/OrraeSans-Regular.ufo"
generated_ufo="$type_root/build/OrraeSans-Regular.ufo"

mkdir -p "$type_root/build" "$type_root/dist"

"$fonttools_python" "$type_root/src/build_font.py" "$generated_ufo"
diff -ru "$canonical_ufo" "$generated_ufo"

"$fontmake_bin" -u "$canonical_ufo" -o ttf \
  --output-path "$type_root/dist/OrraeSans-Regular.ttf" \
  --validate-ufo --no-autohint --production-names
"$fontmake_bin" -u "$canonical_ufo" -o otf \
  --output-path "$type_root/dist/OrraeSans-Regular.otf" \
  --validate-ufo --no-autohint --production-names

"$fonttools_python" "$type_root/src/normalize_font.py" \
  "$type_root/dist/OrraeSans-Regular.ttf" \
  "$type_root/dist/OrraeSans-Regular.otf"

"$fonttools_python" -m fontTools.ttLib.woff2 compress \
  "$type_root/dist/OrraeSans-Regular.ttf" \
  -o "$type_root/dist/OrraeSans-Regular.woff2"
cp "$type_root/src/orrae-sans.css" "$type_root/dist/orrae-sans.css"

"$fonttools_python" -m fontTools.ttx -l "$type_root/dist/OrraeSans-Regular.ttf"
"$fonttools_python" -m fontTools.ttx -l "$type_root/dist/OrraeSans-Regular.otf"
"$fonttools_python" -m fontTools.ttx -l "$type_root/dist/OrraeSans-Regular.woff2"
hb-shape "$type_root/dist/OrraeSans-Regular.ttf" 'HAMBURGEFONS 0123456789'
hb-shape --features=ss01 "$type_root/dist/OrraeSans-Regular.ttf" 'A'

(
  cd "$type_root/dist"
  shasum -a 256 OrraeSans-Regular.ttf OrraeSans-Regular.otf \
    OrraeSans-Regular.woff2 > SHA256SUMS
  shasum -a 256 -c SHA256SUMS
)
