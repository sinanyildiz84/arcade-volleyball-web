"""Reference simulation of the Arcade Volleyball game logic (computer vs computer demo).

bits=16 mimics the cc65 build, bits=32 the Amiga. Used to (a) check the C64
trace matches the source logic, (b) compare rally statistics 16 vs 32 bit.
"""
import sys

JUMP = [-4, -4, -3, -3, -3, -3, -2, -2, -2, -2, -2, -1, -1, -1, -1, -1, -1, 0, 0,
        0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4]
POLECOL = [0, 1, 2, 3, 3, 4, 6, 7, 9, 14]


def cdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def cmod(a, b):
    return a - b * cdiv(a, b)


class Sim:
    def __init__(self, bits, record=False):
        self.bits = bits
        self.x = [0, 0]; self.px = [0, 0]; self.y = [0, 0]; self.fi = [0, 0]
        self.rebound = [0, 0]; self.score = [0, 0]
        self.left = [0, 0]; self.right = [0, 0]; self.up = [0, 0]
        self.bx = self.by = self.pbx = self.pby = self.tbx = self.tby = 0
        self.bvelx = self.bvely = 0
        self.serve = self.server = self.servevel = self.compserve = 0
        self.hits = self.hitter = self.starter = self.sstage = self.bytop = 0
        self.rnd = 0; self.endgame = 0; self.menuon = 1; self.air = 1
        self.frames = 0
        self.record = record
        self.trace = []
        self.rallies = []       # (frame, winner, server_before, scored)
        self.rally_start = 0

    def wrap(self, v):
        m = 1 << self.bits
        v &= m - 1
        return v - m if v >= m >> 1 else v

    def cabs(self, v):
        r = abs(v)
        return self.wrap(r)

    def putshapes(self):
        self.frames += 1
        if self.record:
            self.trace.append((self.tbx, self.tby, self.x[0], self.y[0], self.x[1], self.y[1]))

    def getpos(self):
        for i in range(2):
            if self.up[i] and self.fi[i] == -1:
                self.fi[i] = 0
            velx = self.left[i] + self.right[i]
            tx = self.x[i] + velx
            bnd = 3 + i * 155
            if velx > 0:
                self.x[i] = tx if tx < bnd + 119 else bnd + 119
            else:
                self.x[i] = tx if tx > bnd else bnd
            if self.fi[i] == -2:
                self.y[i] = 173
                self.fi[i] = -1
            if self.fi[i] != -1:
                if self.fi[i] == 19:
                    self.y[i] -= 4
                self.y[i] += JUMP[self.fi[i]]
                self.fi[i] += 1
                if self.fi[i] > 37:
                    self.fi[i] = -2

    def moveball(self):
        rx, ry = self.bvelx, self.bvely
        rx = max(-319, min(319, rx))
        ry = max(-319, min(319, ry))
        self.pbx, self.pby = self.tbx, self.tby
        self.bx += rx
        self.by += ry
        if self.bx < 320:
            self.bx = 320; rx = -rx; rx -= rx >> 4; ry -= ry >> 4
            if self.hitter == 1:
                self.hitter = 2; self.hits = 0
        if self.bx > 18112:
            self.bx = 18112; rx = -rx; rx -= rx >> 4; ry -= ry >> 4
            if self.hitter == 0:
                self.hitter = 2; self.hits = 0
        if self.by < 832:
            self.by = 832; ry = -ry; rx -= rx >> 4; ry -= ry >> 4
        if self.by > 11392:
            self.by = 11392; ry = -ry; hitfloor = 0
        else:
            hitfloor = 1
        ry += 1
        self.tbx = self.bx >> 6
        self.tby = self.by >> 6
        self.bvelx, self.bvely = rx, ry
        return hitfloor

    def docollisions(self):
        for i in range(2):
            dx = self.tbx - self.x[i] - i * 7
            dy = (self.tby - self.y[i]) >> 1
            dist = (dx >> 2) * dx + dy * dy
            if dist < 110:
                rndoff = 8 - (self.rnd & 15)
                if self.fi[i] > -1:
                    self.bvely = -abs(self.bvely) + (JUMP[self.fi[i]] << (3 << self.servevel))
                else:
                    self.bvely = -abs(self.bvely)
                self.bvely += rndoff
                self.bvelx += dx * abs(dx) + ((self.right[i] + self.left[i]) << (4 + self.servevel)) + rndoff
                if not self.rebound[i]:
                    self.bytop = 200; self.serve = 0; self.rebound[i] = 1
                    if self.hitter != i:
                        self.hitter = i; self.hits = 0
                    else:
                        self.hits += 1
            elif self.rebound[i]:
                self.rebound[i] = 0; self.servevel = 0
        i = 1
        if self.tby > 91:
            if self.pbx < 128 and self.tbx > 127:
                self.bvelx = (-abs(self.bvelx)) >> 1; self.bx = 127 * 64; i = 0
            elif self.pbx > 159 and self.tbx < 160:
                self.bvelx = abs(self.bvelx) >> 1; self.bx = 160 * 64; i = 0
        if i and self.tby > 81 and 127 < self.tbx < 160:
            if self.tby > 91:
                self.bvelx = -abs(self.bvelx) if self.tbx < 148 else abs(self.bvelx)
            elif ((self.tbx > 147 and 161 - self.tbx >= POLECOL[91 - self.tby]) or
                  (self.tbx < 148 and self.tbx - 133 >= POLECOL[91 - self.tby])):
                if self.bvely > 0:
                    dx = self.tbx - 145
                    if dx < -5:
                        self.bvelx = -abs(self.bvelx)
                    if dx > 5:
                        self.bvelx = abs(self.bvelx)
                    self.bvely = -abs(self.bvely)
                if abs(self.bvelx) > 32:
                    self.bvelx >>= 1
                if abs(self.bvely) > 32:
                    self.bvely >>= 1

    def resetpt(self):
        i = 1 - self.hitter if self.hits > 2 else int(self.tbx < 150)
        self.putshapes()
        tvely = abs(self.bvely) >> 3
        tvelx = abs(self.bvelx) >> 3
        j = 20
        while True:
            self.up = [0, 0]
            self.getpos()
            if abs(self.bvelx) > tvelx:
                self.bvelx = -tvelx if self.bvelx < 0 else tvelx
            if abs(self.bvely) > tvely:
                self.bvely = -tvely if self.bvely < 0 else tvely
            self.docollisions()
            self.moveball()
            self.putshapes()
            t = j > 0
            j -= 1
            if not (t or self.fi[0] != -1 or self.fi[1] != -1):
                break
        server_before = self.server
        scored = i == self.server
        if scored:
            self.score[i] += 1
            if self.score[i] > 14 and self.score[i] - self.score[1 - i] > 1:
                self.endgame = 1
        else:
            self.server = i
        self.rallies.append((self.frames - self.rally_start, i, server_before, scored))
        if not self.menuon:
            for _ in range(49):
                self.putshapes()
        self.tbx = self.pbx = 64 + i * 165; self.bx = self.tbx << 6
        self.tby = self.pby = 135; self.by = self.tby << 6
        self.bvelx = self.bvely = self.hits = self.rebound[0] = self.rebound[1] = 0
        self.serve = self.servevel = 1; self.hitter = 2
        self.compserve = cmod(self.cabs(self.rnd), 5)
        if self.compserve < 0:
            self.compserve = -self.compserve
        if self.score[self.server] == 14:
            self.compserve = 5
        self.sstage = 0
        self.rally_start = self.frames

    def destination(self, pl, destx, tol):
        xp = self.x[pl]
        if abs(xp - destx) < tol:
            self.left[pl] = 0; self.right[pl] = 0
            return 1
        if xp < destx:
            self.left[pl] = 0; self.right[pl] = 2
        else:
            self.left[pl] = -2; self.right[pl] = 0
        return 0

    def serve_ai(self, pl, table):
        dest = 0
        cs = self.compserve
        if cs in (0, 1, 2):
            dest = self.destination(pl, table[cs], 2)
        elif cs in (3, 4):
            a, b = table[cs]
            if self.sstage == 0:
                dest = self.destination(pl, a, 2)
                if dest:
                    self.sstage = 1
            else:
                self.destination(pl, b, 2)
                dest = 1
        elif cs == 5:
            a, b, sign = table[5]
            if self.sstage == 0:
                if self.destination(pl, a, 2):
                    self.sstage = 1
                dest = 0
            else:
                self.destination(pl, b + sign * self.sstage, 1)
                self.sstage += 1
                dest = 1
        self.up[pl] = dest

    def computer(self, pl):
        self.up[pl] = 0
        if self.tby < self.bytop:
            self.bytop = self.tby
        rndoff = 5 - cmod(self.rnd, 10)
        if self.serve and (self.server & 1) == pl:
            if pl == 0:
                self.serve_ai(0, [55, 84, 80, (44, 58), (90, 58), (3, 8, 1)])
            else:
                self.serve_ai(1, [232, 202, 208, (250, 220), (190, 230), (277, 272, -1)])
            return
        near = self.tbx < 140 if pl == 0 else self.tbx > 125
        if not (self.bvely > 0 and near):
            self.destination(pl, 56 if pl == 0 else 211, 8)
            return
        if (self.bvely >> 6) == 0:
            ystep = 0
        else:
            ystep = cdiv(140 - self.tby, self.bvely >> 6)
        if ystep < 1 or (self.bvelx >> 6) == 0:
            destx = self.tbx
        else:
            destx = self.tbx + (self.bvelx >> 6) * ystep - 4
        dx = self.x[pl] - self.tbx
        if abs(self.bvelx) < 128 and self.bytop < 75:
            a = (self.tby < 158) ^ (self.bvelx < 0)
            if pl == 0:
                self.destination(0, self.tbx - 15 if a else self.tbx + 15, 3)
            else:
                self.destination(1, self.tbx + 15 if a else self.tbx - 15, 3)
        elif self.tby > 130:
            if pl == 0:
                if abs(dx) > 6 and abs(self.bvelx) < 1024:
                    self.destination(0, self.tbx - ((self.x[0] - 60) >> 3), 3)
                else:
                    self.destination(0, self.tbx + rndoff + ((self.x[0] - 60) >> 3), 10)
                    self.up[0] = int(self.x[0] < 105 and (self.hitter != 0 or self.hits < 2))
            else:
                if abs(dx) > 6 and abs(self.bvelx) < 1024:
                    self.destination(1, self.tbx + ((self.x[1] - 218) >> 3), 3)
                else:
                    self.destination(1, self.tbx - rndoff - ((self.x[1] - 218) >> 3), 10)
                    self.up[1] = int(self.x[1] > 175 and (self.hitter != 1 or self.hits < 2))
        else:
            if pl == 0:
                if destx < 3:
                    destx = 6 - destx
                if destx > 123:
                    destx = 246 - destx
                self.destination(0, destx + rndoff, 3)
            else:
                if destx < 158:
                    destx = 316 - destx
                if destx > 277:
                    destx = 554 - destx
                self.destination(1, destx - rndoff, 3)

    def initgame(self):
        self.hits = self.bvelx = self.bvely = self.tby = 0
        self.bytop = 200
        self.x = [64, 226]; self.tbx = 400
        for i in range(2):
            self.px[i] = self.x[i]; self.y[i] = 173; self.fi[i] = -1
            self.rebound[i] = self.score[i] = 0
            self.left[i] = self.right[i] = self.up[i] = 0
        self.putshapes()
        self.tbx = self.pbx = 64 + self.starter * 165; self.bx = self.tbx << 6
        self.tby = self.pby = 135; self.by = self.tby << 6
        self.server = 2 + self.starter; self.hitter = 2; self.serve = self.servevel = 1
        self.rally_start = self.frames

    def run(self, max_frames):
        while self.frames < max_frames:
            self.initgame()
            self.menuon = 1; self.endgame = 0
            while not self.endgame and self.frames < max_frames:
                self.rnd = self.wrap(self.rnd * 5 + 1)
                self.computer(0)
                self.computer(1)
                self.getpos()
                if self.serve:
                    self.docollisions(); self.putshapes(); self.air = 1
                elif self.air:
                    self.docollisions(); self.air = self.moveball(); self.putshapes()
                if not self.air or self.hits > 2:
                    self.resetpt()
            self.starter ^= 1


C64 = {50: (119, 23, 56, 158, 218, 173), 100: (173, 140, 62, 173, 206, 173), 150: (274, 68, 62, 173, 226, 173),
       200: (119, 22, 62, 173, 218, 141), 250: (112, 73, 50, 137, 218, 173), 300: (217, 122, 50, 173, 236, 151),
       350: (31, 127, 48, 173, 218, 173), 400: (272, 93, 50, 173, 238, 173), 450: (57, 47, 66, 173, 218, 169),
       500: (170, 14, 50, 143, 218, 173), 550: (178, 61, 50, 173, 228, 137), 600: (66, 112, 38, 147, 218, 173),
       650: (261, 137, 50, 173, 248, 173), 700: (23, 89, 56, 173, 218, 173), 750: (220, 43, 50, 165, 232, 173),
       800: (109, 26, 50, 173, 218, 139), 850: (131, 64, 50, 137, 218, 173), 900: (207, 114, 50, 173, 226, 149),
       950: (30, 135, 48, 173, 218, 173), 1000: (263, 92, 50, 173, 242, 173), 1050: (66, 42, 64, 173, 218, 169),
       1100: (164, 27, 50, 139, 218, 173), 1150: (191, 85, 50, 173, 226, 139), 1200: (33, 141, 42, 173, 218, 173),
       1250: (274, 90, 50, 173, 232, 173), 1300: (53, 43, 64, 173, 218, 169), 1350: (179, 22, 56, 141, 218, 173),
       1400: (176, 80, 56, 173, 218, 138), 1450: (40, 142, 32, 162, 218, 173), 1500: (283, 95, 50, 173, 232, 173)}

if __name__ == '__main__':
    if len(sys.argv) > 2:           # take the C64 samples from a headless.py log
        import re
        C64 = {}
        pat = re.compile(r'f=\s*(\d+) score=.*?ball=\(\s*(\d+),\s*(\d+)\) p0=\(\s*(\d+),\s*(\d+)\) p1=\(\s*(\d+),\s*(\d+)\)')
        for line in open(sys.argv[2], encoding='utf-8', errors='replace'):
            mt = pat.search(line)
            if mt:
                v = list(map(int, mt.groups()))
                C64[v[0]] = tuple(v[1:])
    import os
    s = Sim(int(os.environ.get('REFSIM_BITS', '16')), record=True)
    s.run(max(C64) + 200)
    best = None
    for off in range(-120, 120):
        ok = 0
        for f, want in C64.items():
            j = f + off
            if any(0 <= k < len(s.trace) and s.trace[k] == want for k in (j - 1, j)):
                ok += 1
        if best is None or ok > best[1]:
            best = (off, ok)
    print(f'16-bit sim vs C64 trace: best offset {best[0]}, {best[1]}/{len(C64)} samples identical')

    frames = int(sys.argv[1]) if len(sys.argv) > 1 else 300000
    for bits in (16, 32):
        s = Sim(bits)
        s.run(frames)
        r = s.rallies
        lens = sorted(n for n, *_ in r)
        scored = sum(1 for *_, sc in r if sc)
        print(f'{bits}-bit: {len(r)} rallies in {frames} frames, points={scored}, '
              f'median rally {lens[len(lens) // 2] if lens else 0} frames, max {lens[-1] if lens else 0}, '
              f'games finished={s.starter}')
