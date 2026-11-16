import json, os, sys, urllib.request

U = os.environ["MAKEFUN_ENV_URL"]


def P(p, b):
    q = urllib.request.Request(U + p, json.dumps(b).encode(), {"content-type": "application/json"})
    return json.load(urllib.request.urlopen(q))


V = {1: 100, 2: 325, 3: 335, 4: 500, 5: 975, 6: 0}
G = {2: (-21, -19, -12, -8, 8, 12, 19, 21),
     3: (-11, -9, 9, 11), 4: (-10, -1, 1, 10),
     5: (-11, -10, -9, -1, 1, 9, 10, 11), 6: (-11, -10, -9, -1, 1, 9, 10, 11)}
CAP = int(os.environ.get("CHESS_CAP", 30000))
N = 0


def fen(s):
    b = [-9] * 120
    r = c = 0
    for ch in s.split()[0]:
        if ch == "/":
            r += 1
            c = 0
        elif ch.isdigit():
            c += int(ch)
        else:
            v = ".PNBRQK".index(ch.upper())
            b[21 + r * 10 + c] = v if ch.isupper() else -v
            c += 1
    return b


def ev(b):
    t = 0
    for i in range(21, 99):
        v = b[i]
        if not v or v == -9:
            continue
        w = abs(v)
        f = i % 10 - 1
        r = i // 10 - 2
        p = V[w]
        if w == 1:
            p += (7 - r if v > 0 else r) * 7 - abs(f - 3) * 2
        elif w == 6:
            p += 35 - (7 - r if v > 0 else r) * 5
        else:
            p += 7 - abs(f - 3) - abs(r - 3)
        t += p if v > 0 else -p
    return t


def gen(b, s):
    o = []
    for i in range(21, 99):
        v = b[i]
        if not v or v == -9 or v * s <= 0:
            continue
        w = abs(v)
        if w == 1:
            j = i - s * 10
            if b[j] == 0:
                o.append((i, j))
            for d in (-11, -9):
                j = i + s * d
                if b[j] * s < 0:
                    o.append((i, j))
        elif w == 2 or w == 6:
            for d in G[w]:
                j = i + d
                if b[j] != -9 and b[j] * s <= 0:
                    o.append((i, j))
        else:
            for d in G[w]:
                j = i + d
                while b[j] == 0:
                    o.append((i, j))
                    j += d
                if b[j] * s < 0:
                    o.append((i, j))
    return o


def mk(b, m):
    i, j = m
    c = b[j]
    v = b[i]
    b[i] = 0
    b[j] = v // abs(v) * 5 if abs(v) == 1 and j // 10 in (2, 9) else v
    return c


def un(b, m, c):
    i, j = m
    b[i] = b[j]
    b[j] = c


def qs(b, s, a, be):
    global N
    N += 1
    st = ev(b) * (1 if s > 0 else -1)
    if st >= be:
        return st
    if st > a:
        a = st
    ms = [m for m in gen(b, s) if b[m[1]] * s < 0]
    ms.sort(key=lambda m: -abs(b[m[1]]))
    for m in ms:
        c = mk(b, m)
        if abs(c) == 6:
            un(b, m, c)
            return 90000
        sc = -qs(b, -s, -be, -a)
        un(b, m, c)
        if sc > a:
            a = sc
            if a >= be:
                break
    return a


def ab(b, s, d, a, be):
    global N
    N += 1
    if N > CAP:
        raise OverflowError
    if d < 1:
        return qs(b, s, a, be)
    ms = gen(b, s)
    ms.sort(key=lambda m: -abs(b[m[1]]))
    best = -99000
    for m in ms:
        c = mk(b, m)
        if abs(c) == 6:
            un(b, m, c)
            return 88000 - d
        sc = -ab(b, -s, d - 1, -be, -a)
        un(b, m, c)
        if sc > best:
            best = sc
        if best > a:
            a = best
        if a >= be:
            break
    if best == -99000:
        return -88000 + d
    return best


def sq(u):
    return 21 + (8 - int(u[1])) * 10 + "abcdefgh".index(u[0])


def best(g):
    global N
    b = fen(g["fen"])
    s = 1 if g["colour"] == "white" else -1
    root = [(u, (sq(u[:2]), sq(u[2:4]))) for u in g["legal_moves"]]
    bw = root[0][0]
    for d in range(1, 7):
        N = 0
        sc = []
        a = -99000
        try:
            for u, m in root:
                c = mk(b, m)
                v = -ab(b, -s, d - 1, -99000, -a)
                un(b, m, c)
                sc.append((v, u))
                if v > a:
                    a = v
        except OverflowError:
            break
        sc.sort(key=lambda x: -x[0])
        bw = sc[0][1]
        if sc[0][0] > 80000:
            break
    return bw


while True:
    g = P("/game", {})
    if g["status"] == "done":
        break
    while g["status"] == "your_move":
        g = P("/move", {"game": g["game"], "move": best(g)})
    print("game %s: %s by %s" % (g["game"], g["outcome"], g["reason"]), file=sys.stderr)
print("done %s-%s-%s" % (g.get("wins"), g.get("draws"), g.get("losses")), file=sys.stderr)
