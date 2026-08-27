# Orrae Sans

Orrae Sans is a wide caps-only display typeface by Orrae Labs. Lowercase code
points intentionally use the uppercase forms.

The public repository contains only the font, its editable source, build and QA
tools, documentation, and license. It contains no Orrae Labs logo or other
brand artwork.

## Character and OpenType support

- Google Fonts Latin Core coverage
- spacing and combining diacritics with `mark` and `mkmk` positioning
- numerals, punctuation, currency, mathematical, and editorial symbols
- custom kerning
- a narrower `A` alternate through Stylistic Set 1 (`ss01`)
- Latin script/language metadata and installable embedding

The typeface is intended for headings, labels, technical markings, and other
deliberate display use. It is not a conventional mixed-case text family.

## Downloads

Prebuilt fonts are published only through [GitHub Releases](../../releases).
Each release provides a versioned `.tar.zst` package containing:

- `OrraeSans-Regular.otf` — recommended for design and print applications
- `OrraeSans-Regular.ttf` — broad desktop and legacy compatibility
- `OrraeSans-Regular.woff2` — web delivery
- `orrae-sans.css` — web-font declaration
- checksums, documentation, authorship files, and `OFL.txt`

An npm-compatible `.tgz` is also built for CDN and package-registry workflows.
It is an artifact only; publishing to npm requires Orrae Labs credentials and
is not performed automatically.

Extract the Zstandard package with:

```sh
zstd -dc orrae-sans-VERSION.tar.zst | tar -xf -
```

Do not install the OTF and TTF simultaneously. They expose the same family and
style names.

## Build from source

The checked-in UFO is the editable interchange source. The Python geometry
generator is also retained and the build refuses to proceed if it does not
reproduce that UFO exactly.

On macOS:

```sh
brew install harfbuzz zstd
python3 -m venv .venv
.venv/bin/pip install --requirement requirements.txt
PATH="$PWD/.venv/bin:$PATH" FONTTOOLS_PYTHON="$PWD/.venv/bin/python" ./src/build-font.sh
```

On Debian or Ubuntu, install `libharfbuzz-bin` and `zstd` instead of the two
Homebrew packages. Generated TTF, OTF, WOFF2, CSS, and checksums are written to
the ignored `dist/` directory.

Verify a local build with:

```sh
cd dist
shasum -a 256 -c SHA256SUMS
```

## Google Fonts QA

FontBakery and `gftools` are pinned separately because their current dependency
ranges conflict. Use independent virtual environments:

```sh
python3 -m venv .fontbakery-venv
.fontbakery-venv/bin/pip install --requirement requirements-fontbakery.txt
.fontbakery-venv/bin/fontbakery check-googlefonts --skip-network \
  dist/OrraeSans-Regular.ttf

python3 -m venv .gftools-venv
.gftools-venv/bin/pip install --requirement requirements-gftools.txt
PATH="$PWD/.gftools-venv/bin:$PATH" .gftools-venv/bin/gftools builder sources/config.yaml
```

The release gate is zero FontBakery failures. Some non-blocking heuristics and
catalog-onboarding checks may remain; their disposition is documented in
[`DISTRIBUTION.md`](DISTRIBUTION.md).

## Automated builds and releases

GitHub Actions rebuilds the font from UFO source and runs FontBakery on every
pull request and push. A signed version tag such as `v1.0.0` additionally
creates a GitHub Release with the `.tar.zst`, npm `.tgz`, and checksums.
Generated binaries are never committed.

## License

Orrae Sans is licensed under the [SIL Open Font License 1.1](OFL.txt), without a
Reserved Font Name. The license permits use, embedding, modification, and
redistribution subject to its terms. Documents and graphics created with the
font are not required to use the OFL.
