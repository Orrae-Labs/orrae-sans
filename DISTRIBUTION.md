# Distribution requirements

Orrae Sans is licensed under the SIL Open Font License 1.1 without a Reserved
Font Name. That is the single license used for the source, generated fonts, and
release packages.

## Compatibility matrix

| Platform | License and intake boundary | Repository or package requirement | Orrae Sans status |
| --- | --- | --- | --- |
| Google Fonts | New families must use OFL 1.1; the license covers the entire family. | Editable source, reproducible build, canonical metadata, GF Latin Core coverage, installable embedding, compatible vertical metrics, and FontBakery validation. Google serves TTFs. | Ready at the upstream-repository level. A submission still requires the Google Fonts issue/PR process and contributor agreement. |
| Fontsource | Accepts open-source fonts, including OFL families not already available through Google Fonts. | A Fontsource font request and upstream source URL; Fontsource generates its own npm packages, subsets, CSS, and web formats. | License and upstream source are compatible. |
| Bunny Fonts | Serves open-source fonts and tracks the Google Fonts/Fontsource ecosystem. | Inclusion occurs through Bunny's catalog pipeline rather than by uploading this release archive. | License and character coverage are compatible. |
| Font Squirrel | Redistributes fonts whose license permits web embedding and redistribution. | Human review and a clear redistribution license; desktop font files are expected. | OFL, OTF, and TTF releases are compatible. Acceptance remains editorial. |
| npm | Requires a valid package manifest and a license that permits redistribution. | The package must contain its generated web font and CSS at publish time. | `package.json` is ready; CI creates an npm-compatible `.tgz`. Publishing credentials are intentionally not configured. |
| jsDelivr / unpkg | Serve public npm packages; jsDelivr can also serve tagged public GitHub files. | A public npm package or stable GitHub tag. | Ready once an npm package is published; GitHub Releases remain the primary download channel. |
| GitHub Releases / self-hosting | No font-specific intake rules beyond lawful redistribution. | Standalone fonts, license, CSS, checksums, and stable versioned artifacts. | Fully supported by the release workflow. |
| MyFonts / Monotype | MyFonts does not accept a family that is entirely free and available from other websites. | A separate commercial foundry agreement and commercial distribution strategy. | Deliberately incompatible with the open distribution plan; this is a platform policy conflict, not an OFL defect. |
| Adobe Fonts | Inclusion is governed by Adobe's foundry licensing and onboarding process. | A separate relationship with Adobe; an open license does not itself cause catalog inclusion. | The OFL does not prevent discussion with Adobe, but there is no self-service submission path represented here. |

## Google Fonts technical baseline

The deterministic build enforces the strictest reusable baseline among these
platforms:

- SIL OFL 1.1 in `OFL.txt` and matching name-table metadata;
- no Reserved Font Name;
- editable UFO source plus a `gftools builder` configuration;
- version 1.000 naming, canonical family/style/PostScript names, and Regular
  style linking;
- GF Latin Core coverage, including spacing and combining marks;
- `mark`/`mkmk`, GDEF, kerning, and a named `ss01` alternate;
- `OS/2.fsType = 0`, Latin code-page coverage, and Use Typo Metrics;
- equal hhea/typo vertical metrics with zero line gaps;
- deterministic timestamps, unhinted-font `gasp`/`prep`, and Latin script tags;
- TTF, OTF, WOFF2, CSS, checksums, an OFL-bearing Zstandard archive, and an
  npm-compatible package generated only in CI;
- a zero-failure Google Fonts FontBakery gate.

Google-specific `METADATA.pb`, catalog article assets, designer profile, and
the pull request are intentionally left to Google's onboarding repository and
review process. Generated binaries remain absent from this source repository.

## Manual gates

The following cannot be made automatic or guaranteed by a source repository:

- Google Fonts contributor agreement, intake issue, and review;
- Fontsource request and review;
- Bunny Fonts catalog synchronization;
- Font Squirrel editorial acceptance;
- npm organization access and publish token;
- Microsoft vendor-ID registration;
- any Adobe Fonts or Monotype commercial agreement.

## Authoritative references

- [SIL Open Font License 1.1](https://openfontlicense.org/)
- [Google Fonts: license file](https://googlefonts.github.io/gf-guide/license-file.html)
- [Google Fonts: font requirements](https://googlefonts.github.io/gf-guide/requirements.html)
- [Google Fonts: upstream repository](https://googlefonts.github.io/gf-guide/upstream.html)
- [Google Fonts: production process](https://googlefonts.github.io/gf-guide/production.html)
- [Fontsource project and new-font intake](https://github.com/fontsource/fontsource#adding-new-fonts)
- [Bunny Fonts FAQ](https://fonts.bunny.net/faq)
- [Font Squirrel licensing FAQ](https://www.fontsquirrel.com/faq)
- [npm package license field](https://docs.npmjs.com/cli/v11/configuring-npm/package-json#license)
- [jsDelivr package documentation](https://www.jsdelivr.com/documentation)
- [unpkg package CDN](https://unpkg.com/)
- [Microsoft registered font vendors](https://learn.microsoft.com/en-us/typography/vendors/)
- [MyFonts/Monotype free-font policy](https://foundrysupport.monotype.com/hc/en-us/articles/360041729651-Free-Fonts)
- [Adobe Fonts licensing](https://helpx.adobe.com/fonts/using/font-licensing.html)
