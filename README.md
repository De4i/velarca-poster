# Velarca — a travel poster for a place that isn't there

[![the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/De4i/velarca-poster/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/De4i/velarca-poster/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)

Velarca is an invented bay whose one landmark is a great natural stone
arch standing in a turquoise lagoon. The poster shows the place at
sunset: the low sun framed inside the arch's opening, a whitewashed
terraced village with a chapel bell tower climbing the dark headland to
the left, two sailboats on the water, and a gold sun path across the
lagoon. The place's name is the only copy on the poster, set large in
cream serif capitals above a gold rule, in the manner of a vintage
travel poster.

`main.ts` (Node, standard library only) copies the baked `entry.png`
beside it to `$MAKEFUN_OUTPUT_DIR/entry.png`, or to
`/output/entry.png` when the variable is not set, creating the output
directory if needed and leaving the file readable by everyone. The
output is byte-identical on every run. The poster itself is rendered
by `poster/build_poster.py` (Pillow, deterministic, no network).

Competition: [the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)

## Run

```sh
node main.ts
```

## Rebuild the poster

```sh
python3 poster/build_poster.py
```

That re-renders `entry.png` at the repository root: 1024×1024, well
under the 1 MiB limit, byte-identical across runs.

## License

MIT — see [LICENSE](LICENSE).
