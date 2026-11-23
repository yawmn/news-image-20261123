# The World — 23 November 2026

A single-page, fully procedural summary of the world news of Monday, 23 November 2026,
built for make.fun's daily news-image bounty.

The entry is `main.py` (Python 3.13, standard library only). It rasterises every shape
and glyph outline itself, deflates the PNG and writes `/output/entry.png`. It uses no
network, clock or randomness, so two runs produce byte-identical output.

Run it locally:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Stories shown: Iran's claimed strikes on US bases in Bahrain and the Hormuz shipping
crisis; COP31's collapse in Antalya; suspected Ukrainian sea-drone strikes on the
Russian corvette Merkury at Benghazi and Odesa's blackouts; India–China corps-commander
talks on the Arunachal frontier; Nepal's PM Balendra Shah meeting Narendra Modi in
Delhi; and the US probe into an alleged Chinese spy tied to Nvidia's former CEO.
Secondary line: Israel's stalled coalition talks, West Bank settler arson, and Haiti's
hunger crisis.

Typography uses flattened outlines from the DejaVu fonts (Bitstream Vera licence);
see `NOTICE`.
