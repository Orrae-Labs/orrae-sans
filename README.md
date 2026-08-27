# Orrae Sans

Orrae Sans is a custom caps-only typeface by Orrae Labs, extended into a
deterministic display system.

## Included

- A–Z
- numerals 0–9
- essential punctuation
- lowercase code points mapped to uppercase forms
- custom kerning
- a narrower `A` alternate through OpenType Stylistic Set 1 (`ss01`)

This initial release is intended for titles, hardware markings, and other
deliberate display use.

## Downloads

- [`OrraeSans-Regular.otf`](dist/OrraeSans-Regular.otf) — recommended for
  design and print applications
- [`OrraeSans-Regular.ttf`](dist/OrraeSans-Regular.ttf) — broad desktop and
  legacy application compatibility
- [`OrraeSans-Regular.woff2`](dist/OrraeSans-Regular.woff2) — web delivery
- [`orrae-sans.css`](dist/orrae-sans.css) — web font declaration

Do not install the OTF and TTF simultaneously. They expose the same family and
style names.

## Reproducible build

On macOS with Homebrew:

```sh
brew install fonttools fontforge woff2 harfbuzz
./src/build-font.sh
```

The build regenerates the TTF, OTF, and WOFF2 from source. TTF and OTF outputs
are checked with FontForge `fontlint`; WOFF2 tables and OpenType shaping are
also verified.

Verify the committed release files with:

```sh
cd dist
shasum -a 256 -c SHA256SUMS
```

The deterministic source is canonical. OTF, TTF, and WOFF2 files are generated
deliverables.

## Automated builds and releases

GitHub Actions rebuilds and validates the font on every pull request and push.
Pushing a version tag such as `v0.2.0` also creates a GitHub Release containing
font-only ZIP and tar.gz download packages plus checksums.

## License

Copyright © 2026 Orrae Labs LLC. All rights reserved. See [`LICENSE`](LICENSE).
