#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
version=${1:-dev}
package_name="orrae-sans-${version#v}"
stage_dir="$project_root/release/$package_name"

rm -rf "$project_root/release"
mkdir -p "$stage_dir"

cp "$project_root/dist/OrraeSans-Regular.otf" "$stage_dir/"
cp "$project_root/dist/OrraeSans-Regular.ttf" "$stage_dir/"
cp "$project_root/dist/OrraeSans-Regular.woff2" "$stage_dir/"
cp "$project_root/dist/orrae-sans.css" "$stage_dir/"
cp "$project_root/dist/SHA256SUMS" "$stage_dir/"
cp "$project_root/README.md" "$stage_dir/"

if [[ -f "$project_root/OFL.txt" ]]; then
  cp "$project_root/OFL.txt" "$stage_dir/"
else
  cp "$project_root/LICENSE" "$stage_dir/"
fi

(
  cd "$project_root/release"
  COPYFILE_DISABLE=1 tar -cf - "$package_name" | \
    zstd -19 --threads=0 --no-progress -o "$package_name.tar.zst"
  shasum -a 256 "$package_name.tar.zst" > SHA256SUMS
  shasum -a 256 -c SHA256SUMS
  zstd --test "$package_name.tar.zst"
  zstd -dc "$package_name.tar.zst" | tar -tf - >/dev/null
)
