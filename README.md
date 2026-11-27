# The World in One Day — Thursday 26 November 2026

[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/akbare12/news-26-b10-numbers/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/akbare12/news-26-b10-numbers/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

One image summing up the world's news of **Thursday 26 November 2026**:
50 stories across 15+ regions, drawn from Reuters, AP, BBC, CNN, NPR,
UKMTO, ONS, KCNA and the FCC.

## The day in three stories

- **Macy's 100th Thanksgiving Parade postponed** — the first weather
  postponement in the parade's history. A big East Coast storm brings
  gusts to 60 mph; the parade moves to Saturday 28 Nov, 08:30 ET.
- **IRGC claims 2 tankers hit by mines in the Strait of Hormuz** — a
  supertanker carrying 2 million barrels among them. The claim is
  unverified; UKMTO confirmed a projectile blast west of Dubai.
- **Global markets rebound** as the Trump tariff salvo on 14 partners
  (China 20%) lands softer than feared: STOXX 600 +1.6%, MSCI +0.4%.

Ten more stories get their own card (Gaza, Kyiv, Bogor, Jerusalem,
Pyongyang, Washington, London, Moscow, Bangkok, Germany) and 37 further
stories run in the ALSO lists — 19 in the right column, 18 continued
in the band above the map. Every card and ALSO item carries a
literal tag: [C] confirmed, [R] reported, [CL] claim (unverified).
A two-line DATE CHECK names the big stories that are *not* 26 November
news (COP31 failed 22 Nov, Shenzhou-24 launched 25 Nov, and others),
so the date the image sums up is unambiguous.

## Layout (V8)

Masthead on top, DATE CHECK in two lines below it, then a two-column
split: the left 60% holds the tall Macy's hero over a 2×5 card grid,
the right 40% stacks the Hormuz and tariffs heroes over the ALSO list.
A full-width world-map strip with numbered pins, a thin timeline
strip and a sources footer close the page.

## How it is built

- `gen.py` (Pillow, build time only) renders `entry.png` at 1024×1024.
  It measures every string with PIL font metrics and asserts it fits
  its box, clamps every scene into its own art layer so art can never
  cover text, and scans the 37 ALSO items for duplicates against the
  heroes and cards (0 flags).
- `main.py` is standard library only (`os`/`shutil`): it copies
  `entry.png` into `MAKEFUN_OUTPUT_DIR`. The grader runs with no
  network and nothing installed, so no PIL import is allowed here.

Run it:

```
python3 gen.py
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Verification

- `entry.png`: 1024×1024, 232031 bytes,
  sha256 `87ba2759884db9b724567776841b1f1e4d035c9ba48cf95cda2eb17eccacab99`
- Stories: 3 heroes + 10 cards + 37 ALSO = 50; regions 15+
- Duplicate scan (ALSO vs heroes/cards, ≥3 shared distinctive words):
  0 flags; no literal duplicate ALSO item
- All text measured to fit its box at build time (gen.py asserts)
- Stdlib-venv simulation (27 Nov 2026): venv without Pillow (`import PIL`
  fails), different cwd, read-only repo copy, empty out dir — 2 runs,
  both exit 0, output sha256 identical to `entry.png` above

## License

MIT — see `LICENSE`.
