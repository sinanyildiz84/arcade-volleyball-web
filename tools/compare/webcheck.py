"""Compare a trace taken from the browser port with the original game's logic.

The browser trace comes from web/game.js via its AVB.step()/AVB.state() hook
(see README); refsim.Sim(32) is the Amiga reference. Both start from the same
state (rnd 0, computer vs computer demo), so the two traces must be identical.

usage: webcheck.py browser_trace.txt
       each line: step tbx tby x0 y0 x1 y1 score0 score1 server
"""
import sys

from refsim import Sim

rows = []
for line in open(sys.argv[1]):
    p = line.split()
    if len(p) == 10:
        rows.append([int(v) for v in p])
if not rows:
    sys.exit('no trace rows')

sim = Sim(32, record=True)
sim.run(rows[-1][0] + 100)

ok = bad = 0
first_bad = None
for step, tbx, tby, x0, y0, x1, y1, s0, s1, server in rows:
    got = (tbx, tby, x0, y0, x1, y1)
    want = sim.trace[step - 1]          # trace[0] is the state after step 1
    if got == want:
        ok += 1
    else:
        bad += 1
        if first_bad is None:
            first_bad = (step, got, want)
print(f'browser vs Amiga reference: {ok}/{ok + bad} sampled steps identical')
if first_bad:
    print(f'first difference at step {first_bad[0]}: browser {first_bad[1]}, reference {first_bad[2]}')
print(f'last sample: step {rows[-1][0]}, score {rows[-1][7]}:{rows[-1][8]}, server {rows[-1][9]}')
