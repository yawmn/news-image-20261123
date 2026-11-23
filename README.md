# The World — 23 November 2026

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/yawmn/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/yawmn/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

A single-page, fully procedural summary of the world news of Monday, 23 November 2026,
built for [make.fun](https://make.fun/bounty/news-image-20261123)'s daily news-image bounty.

The entry is `main.py` (Python 3.13, standard library only). It rasterises every shape
and glyph outline itself, deflates the PNG and writes `/output/entry.png`. It uses no
network, clock or randomness, so two runs produce byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Stories shown: Iran's claimed strikes on US bases in Bahrain and the Hormuz shipping
crisis; COP31's collapse in Antalya; suspected Ukrainian sea-drone strikes on the
Russian corvette Merkury at Benghazi and Odesa's blackouts; India–China corps-commander
talks on the Arunachal frontier; Nepal's PM Balendra Shah meeting Narendra Modi in
Delhi; and the US probe into an alleged Chinese spy tied to Nvidia's former CEO.
Secondary line: Israel's stalled coalition talks, West Bank settler arson, and Haiti's
food crisis.

Typography uses flattened outlines from the DejaVu fonts (Bitstream Vera licence);
see `NOTICE`.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
