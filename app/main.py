from collections.abc import Mapping as M
import readline as r
import shlex as s
import subprocess as u
import sys as y
import pathlib as p
import os as o
from typing import Final as F, TextIO as T
from io import StringIO as I

A: F[list[str]] = ["echo", "exit", "type", "pwd", "cd"]


def B(C: str, D: dict[str, p.Path]) -> None:
    E = p.Path(C)
    if E.exists() and E.is_dir():
        for F_ in E.iterdir():
            if F_.is_file() and o.access(F_, o.X_OK):
                D[F_.name] = F_


def G() -> M[str, p.Path]:
    H: dict[str, p.Path] = {}
    for I_ in (o.getenv("PATH") or "").split(":"):
        B(I_, H)
    return H


J: F[M[str, p.Path]] = {**G()}
K: F[list[str]] = [*A, *J.keys()]


def L(M_, N, O):
    print()
    if N:
        print("  ".join(N))
    print("$ " + M_, end="")


def P(Q: str, R: int) -> str | None:
    S = list(set([T for T in K if T.startswith(Q)]))
    if len(S) == 1:
        return S[R] + " " if R < len(S) else None
    return S[R] if R < len(S) else None


r.set_completion_display_matches_hook(L)
r.parse_and_bind("tab: complete")
r.set_completer(P)


def main():
    while True:
        y.stdout.write("$ ")
        U = s.split(input())
        V = y.stdout
        W = y.stderr
        X = False
        Z = False
        try:
            for a, b, c, d in [(">", "w", "V", "X"), ("1>", "w", "V", "X"), ("2>", "w", "W", "Z"),
                               (">>", "a", "V", "X"), ("1>>", "a", "V", "X"), ("2>>", "a", "W", "Z")]:
                if a in U:
                    e = U.index(a)
                    f = open(U[e + 1], b)
                    if c == "V":
                        V, X = f, True
                    else:
                        W, Z = f, True
                    U = U[:e] + U[e + 2:]
            if "|" in U:
                g, h = [], []
                for i in U:
                    if i == "|":
                        g.append(h);
                        h = []
                    else:
                        h.append(i)
                g.append(h)
                q(g, V, W)
            else:
                j(U, V, W)
        finally:
            if X: V.close()
            if Z: W.close()


def j(k: list[str], l: T, m: T):
    match k:
        case ["echo", *n]:
            l.write(" ".join(n) + "\n")
        case ["type", z_]:
            t(z_, l, m)
        case ["exit", "0"]:
            y.exit(0)
        case ["pwd"]:
            l.write(f"{o.getcwd()}\n")
        case ["cd", p_]:
            v(p_, l, m)
        case [q_, *r]:
            if q_ in J:
                s_ = u.Popen([q_, *r], stdout=l, stderr=m)
                s_.wait()
            else:
                l.write(f"{' '.join(k)}: command not found\n")


def w(x: str) -> bool:
    return x in A


def y_(z: list[str], aa: T, ab: T, ac: T):
    if not z: return
    if w(z[0]):
        ad, ae, af = y.stdin, y.stdout, y.stderr
        y.stdin, y.stdout, y.stderr = aa, ab, ac
        try:
            j(z, ab, ac)
        finally:
            y.stdin, y.stdout, y.stderr = ad, ae, af
    elif z[0] in J:
        u.run(z, stdin=aa, stdout=ab, stderr=ac)
    else:
        ac.write(f"{z[0]}: command not found\n")


def q(ag: list[list[str]], ah: T, ai: T):
    aj = []
    ak = len(ag)
    al = None
    for am, an in enumerate(ag):
        if am == 0:
            ao, ap = o.pipe()
            if w(an[0]):
                with o.fdopen(ap, 'w') as aq:
                    y_(an, y.stdin, aq, ai)
                al = o.fdopen(ao)
            else:
                ar = u.Popen(an, stdout=ap, stderr=ai, close_fds=True)
                o.close(ap)
                al = o.fdopen(ao)
                aj.append(ar)
        elif am == ak - 1:
            y_(an, al, ah, ai)
            if al: al.close()
        else:
            as_, at = o.pipe()
            if w(an[0]):
                with o.fdopen(at, 'w') as au:
                    y_(an, al, au, ai)
                if al: al.close()
                al = o.fdopen(as_)
            else:
                av = u.Popen(an, stdin=al, stdout=at, stderr=ai, close_fds=True)
                if al: al.close()
                o.close(at)
                al = o.fdopen(as_)
                aj.append(av)
    for aw in aj:
        aw.wait()


def t(ax: str, ay: T, az: T):
    if ax in A:
        ay.write(f"{ax} is a shell builtin\n")
        return
    if ax in J:
        ay.write(f"{ax} is {J[ax]}\n")
        return
    ay.write(f"{ax}: not found\n")


def v(ba: str, bb: T, bc: T) -> None:
    if ba.startswith("~"):
        bd = o.getenv("HOME") or "/root"
        ba = ba.replace("~", bd)
    be = p.Path(ba)
    if not be.exists():
        bb.write(f"cd: {ba}: No such file or directory\n")
        return
    o.chdir(be)


if __name__ == "__main__":
    main()
