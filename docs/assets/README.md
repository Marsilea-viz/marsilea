# Vendored documentation assets

Third-party images and fonts the gallery renders, checked in so the docs build
never fetches them.

Read the Docs builds were failing with HTTP 429 from `upload.wikimedia.org`, and
every build otherwise pinned its output to whatever five third-party hosts served
that day — Font Awesome in particular was pulled from a moving `6.x` branch.

`docs/source/conf.py` copies these into the caches the loaders read from
(`_seed_asset_caches`) before Sphinx runs, so the examples keep their original
URLs and keep demonstrating that `Image` accepts one.

## Adding an image

Download it, drop it in `images/`, add a `filename: url` line to
`images/sources.json`. The URL string must match the one in the example exactly —
it is the cache key.

## `images/`

`images/sources.json` maps each file to its source URL.

Twemoji (`1f*.png`), from <https://github.com/twitter/twemoji> via jsDelivr —
graphics licensed CC-BY 4.0, copyright Twitter and other contributors.

The remaining files are Wikimedia Commons thumbnails of programming language
logos. They are the marks of their respective owners, reproduced here to identify
the languages they name. Individual licence terms are on each file's Commons
page; follow the URL in `sources.json` and strip the `/thumb/.../250px-*` part to
reach it.

## `fonts/`

| File | Source | Licence |
| --- | --- | --- |
| `Lato.zip` | Google Fonts | SIL Open Font License 1.1 |
| `Roboto Mono.zip` | Google Fonts | Apache License 2.0 |
| `fa-brands-400.ttf`, `fa-regular-400.ttf`, `fa-solid-900.ttf` | [Font Awesome Free 6.x](https://github.com/FortAwesome/Font-Awesome) | SIL Open Font License 1.1 |

The Google Fonts archives are shipped exactly as downloaded — `mpl_fontkit`
extracts the zip, and repacking a subset risks dropping a weight the gallery
asks for. Each archive carries its own licence file.
