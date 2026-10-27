# Arcade Volleyball — browser port

*Arcade Volleyball* (COMPUTE! Publications, 1989) running in a browser, on a
phone, a tablet or a desktop. Translated from the Amiga source code that was
published on the Compute's Amiga Resource Fall 1989 cover disk.

**Play:** open `index.html` from a web server (or the published page), or
download `arcade-volleyball.html` — a single file with everything inside,
which plays offline with no server and nothing to install.

## Controls

| | |
|---|---|
| Menu | ▲ ▼ and START, or tap a line; arrow keys and space |
| Move | ◀ ▶ buttons, or ← → |
| Jump | JUMP button, space or ↑ |
| Pause / back to the menu | the II and MENU buttons in the title bar; P and Esc |

Two people can play on one device: pick *Human vs. Human* and each side gets
its own buttons. On a keyboard the left player uses **A**, **D** and **W**.

## Offline and installing

The hosted version is a PWA: the first visit caches the whole game with a
service worker, and after that it runs with no connection. On Android and
desktop Chrome an **Install** button appears; on iOS use Share → Add to Home
Screen. The single-file `arcade-volleyball.html` needs none of that — save it
and open it whenever you like.

## How it was made

* **The game logic is the original C**, translated line for line. The Amiga
  ran one iteration of the main loop per vertical blank, and some functions
  (`resetpt()`, the menu) wait for the display inside nested loops, so every
  function that called `putshapes()` is a JavaScript generator here and
  `putshapes()` is a `yield`: one yield = one frame = one `WaitBOVP()`. The
  host loop advances the generator 50 times a second, as on a PAL Amiga.
* **The graphics are the original sprites.** `tools/mkweb.py` reads the
  32x26 three-colour sprite pairs straight out of the Amiga source and writes
  `sprites.js`, so the players and the ball are pixel for pixel what the
  Amiga drew — unlike the C64 port, which has to shrink them to 24x21. The
  court, the net and the text are drawn at the Amiga's coordinates with the
  colours from its `SetRGB4()` calls.
* **The sound** is three Web Audio recreations of the Amiga samples: a knock
  for a header, a falling buzz for a lost serve, a whistle for a point.

## Is it faithful?

Yes, to the frame. `tools/compare/webcheck.py` compares a trace taken from
this port (via the `AVB.step()` / `AVB.state()` hook, with `?manual` in the
URL so the clock does not run) against a reference implementation of the
original logic. 120 of 120 sampled steps over a 3000 step demo match exactly,
including the point scored and the serve changing hands.

To repeat it:

```
python -m http.server 8787        # in this folder
# open http://127.0.0.1:8787/index.html?manual and run in the console:
#   const out=[]; for (let i=1;i<=3000;i++){ AVB.step();
#     if (i%25===0){ const s=AVB.state();
#       out.push(`${i} ${s.tbx} ${s.tby} ${s.x0} ${s.y0} ${s.x1} ${s.y1} ${s.score0} ${s.score1} ${s.server}`); } }
#   copy(out.join('\n'))
python tools/compare/webcheck.py trace.txt
```

## Building

`index.html`, `game.js` and `sw.js` are written by hand; the rest is generated:

```
python tools/mkweb.py path/to/ArcadeVolleyball.c .   # sprites.js, icons
python tools/mkstandalone.py .                       # arcade-volleyball.html
```

`ArcadeVolleyball.c` is the original Amiga source from the Compute's Amiga
Resource Fall 1989 cover disk; it is not included here. It can be found on
that disk or in [raphnet's Master System port](https://github.com/raphnet/arcadevolleyball).

Bump `CACHE` in `sw.js` when you change a file, or browsers will keep serving
the cached copy.

## Credits

Original game: Copyright 1989 COMPUTE! Publications, Inc. All rights reserved.
Published with its source code in Compute's Amiga Resource, Fall 1989.
