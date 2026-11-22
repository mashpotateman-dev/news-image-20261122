# 22 November 2026 — World News in One Image

[![competition](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/c/news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/mashpotateman-dev/news-image-20261122/rank.svg)](https://make.fun/c/news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/mashpotateman-dev/news-image-20261122/reward.svg)](https://make.fun/c/news-image-20261122)

Entry for the make.fun bounty [Sum up 22 November's world news in one image](https://make.fun/c/news-image-20261122).

`main.py` (Python 3.13, standard library only, no network) draws a 1024x1024
newspaper front page and writes it to `/output/entry.png`. The output is
deterministic: two runs write identical bytes.

The four stories:

1. **COP31 climate talks stall** — no fossil-fuel deal in Turkey
2. **Iran strikes Bahrain** — missiles hit an industrial site, 2 hurt
3. **Mexico captures El Chapo Isidro** — cartel boss caught, 11 dead
4. **Markets fall** — S&P 500 down 3.7% in AI sell-off

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`MAKEFUN_OUTPUT_DIR` stands in for `/output` outside the grader.

## License

MIT
