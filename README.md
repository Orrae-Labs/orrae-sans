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

Prebuilt fonts are published only through [GitHub Releases](../../releases).
Each release provides a versioned `.tar.zst` package containing:

- `OrraeSans-Regular.otf` — recommended for design and print applications
- `OrraeSans-Regular.ttf` — broad desktop and legacy compatibility
- `OrraeSans-Regular.woff2` — web delivery
- `orrae-sans.css` — web-font declaration
- checksums, documentation, and the applicable license

Extract a package with:

```sh
zstd -dc orrae-sans-VERSION.tar.zst | tar -xf -
```

Do not install the OTF and TTF simultaneously. They expose the same family and
style names.

## Reproducible build

On macOS with Homebrew:

```sh
brew install fonttools fontforge woff2 harfbuzz
./src/build-font.sh
```

The build regenerates the TTF, OTF, and WOFF2 into the ignored `dist/`
directory. TTF and OTF outputs are checked with FontForge `fontlint`; WOFF2
tables and OpenType shaping are also verified.

Verify a local build with:

```sh
cd dist
shasum -a 256 -c SHA256SUMS
```

The deterministic source is canonical. Generated font binaries are never
committed.

## Automated builds and releases

GitHub Actions rebuilds and validates the font on every pull request and push.
Pushing a version tag such as `v0.2.0` also creates a GitHub Release containing
a font-only `.tar.zst` package plus its checksum.

## License

Copyright © 2026 Orrae Labs LLC. All rights reserved. See [`LICENSE`](LICENSE).
