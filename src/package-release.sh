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
cp "$project_root/AUTHORS.txt" "$stage_dir/"
cp "$project_root/CONTRIBUTORS.txt" "$stage_dir/"
cp "$project_root/CHANGELOG.md" "$stage_dir/"
cp "$project_root/DESCRIPTION.en_us.html" "$stage_dir/"

cp "$project_root/OFL.txt" "$stage_dir/"

(
  cd "$project_root/release"
  if command -v gtar >/dev/null 2>&1; then
    tar_bin=gtar
  else
    tar_bin=tar
  fi

  if "$tar_bin" --version 2>/dev/null | grep -q 'GNU tar'; then
    "$tar_bin" --sort=name --mtime='UTC 2026-08-26' \
      --owner=0 --group=0 --numeric-owner -cf - "$package_name" | \
      zstd -19 --threads=0 --no-progress -o "$package_name.tar.zst"
  else
    COPYFILE_DISABLE=1 "$tar_bin" -cf - "$package_name" | \
      zstd -19 --threads=0 --no-progress -o "$package_name.tar.zst"
  fi

  cd "$project_root"
  npm pack --pack-destination "$project_root/release" >/dev/null
  cd "$project_root/release"
  shasum -a 256 "$package_name.tar.zst" ./*.tgz > SHA256SUMS
  shasum -a 256 -c SHA256SUMS
  zstd --test "$package_name.tar.zst"
  zstd -dc "$package_name.tar.zst" | tar -tf - >/dev/null
)
