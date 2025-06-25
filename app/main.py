import sys as qznq
import os as xzqz
import shutil as yqzn
import subprocess as pqzq
from pathlib import Path as nqpp
from copy import copy as bqqw
import readline as qwpz


def xqwp(qpwp, nbnb=False):
    wqwp = str()
    qqwp = []
    xwqp = False
    pqwp = False
    nqpq = False
    for ewqw, zwqq in enumerate(qpwp):
        if nqpq:
            nqpq = False
            continue
        if zwqq == "'":
            if pqwp:
                wqwp += zwqq
            elif xwqp:
                xwqp = False
            else:
                xwqp = True
            continue
        if zwqq == '"':
            if xwqp:
                wqwp += zwqq
            elif pqwp:
                pqwp = False
            else:
                pqwp = True
            continue
        if ord(zwqq) == 92:
            if xwqp:
                wqwp += zwqq
            elif pqwp:
                if qpwp[ewqw + 1] in (chr(92), '$', '"'):
                    wqwp += qpwp[ewqw + 1]
                    nqpq = True
                else:
                    wqwp += zwqq
            else:
                wqwp += qpwp[ewqw + 1]
                nqpq = True
            continue
        if not any([xwqp, pqwp]):
            if zwqq == ' ':
                qqwp.append(wqwp)
                wqwp = str()
            else:
                wqwp += zwqq
        else:
            wqwp += zwqq
    qqwp.append(wqwp)
    while '' in qqwp:
        qqwp.remove('')
    return qqwp if nbnb else ' '.join(qqwp)


def pqpp(zqpp):
    zqzq = ['>', '1>', '2>', '>>', '1>>', '2>>']
    aqaq = False
    qqzq = False
    for iwqw, eqwe in enumerate(zqpp):
        if eqwe == '>' and iwqw:
            if zqpp[iwqw - 1] == '2':
                qqzq = True
                break
    if any(i in zqpp for i in zqzq):
        if '2>>' in zqpp:
            zqz = zqpp.split('2>>', 1)
            pqpq = zqz[0].strip()
            qzqq = zqz[1].strip()
            aqaq = True
            qqzq = True
        elif '2>' in zqpp:
            zqz = zqpp.split('2>', 1)
            pqpq = zqz[0].strip()
            qzqq = zqz[1].strip()
            aqaq = False
            qqzq = True
        elif '1>>' in zqpp:
            zqz = zqpp.split('1>>', 1)
            pqpq = zqz[0].strip()
            qzqq = zqz[1].strip()
            aqaq = True
        elif '>>' in zqpp:
            zqz = zqpp.split('>>', 1)
            pqpq = zqz[0].strip()
            qzqq = zqz[1].strip()
            aqaq = True
        elif '1>' in zqpp:
            zqz = zqpp.split('1>', 1)
            pqpq = zqz[0].strip()
            qzqq = zqz[1].strip()
            aqaq = False
        else:
            zqz = zqpp.split('>', 1)
            pqpq = zqz[0].strip()
            qzqq = zqz[1].strip()
            aqaq = False
    else:
        return (zqpp, None, False, False)
    return (pqpq, qzqq, aqaq, qqzq)


def azaz(bqaz, dqaz, xqaz=False):
    zqaz = bqaz[::-1].split(chr(47), 1)[1][::-1]
    pqaz = bqaz[::-1].split(chr(47), 1)[0][::-1]
    xzqz.chdir(zqaz.strip())
    open(pqaz, 'a' if xqaz else 'w').write(str(dqaz))
    return None


def wwww(zzzz):
    zzzzq = len(zzzz)
    yyyyy = []
    for _ in range(zzzzq - 1):
        yyyyy.append(xzqz.pipe())
    ddddd = {'exit', 'echo', 'type', 'pwd', 'cd', 'history'}
    ppppp = []
    for i, cmd in enumerate(zzzz):
        args = xqwp(cmd, nbnb=True)
        jjjjj = args[0] in ddddd
        if jjjjj and zzzzq == 1:
            return
        pid = xzqz.fork()
        if pid == 0:
            if i > 0:
                xzqz.dup2(yyyyy[i - 1][0], 0)
            if i < zzzzq - 1:
                xzqz.dup2(yyyyy[i][1], 1)
            for r, w in yyyyy:
                xzqz.close(r)
                xzqz.close(w)
            if jjjjj:
                if args[0] == 'echo':
                    print(' '.join(args[1:]))
                elif args[0] == 'pwd':
                    print(xzqz.getcwd())
                elif args[0] == 'type':
                    sss = args[1] if len(args) > 1 else ''
                    if sss in ddddd:
                        print(f'{sss} is a shell builtin')
                    elif bbbb := yqzn.which(sss):
                        print(f'{sss} is {bbbb}')
                    else:
                        print(f'{sss}: not found')
                xzqz._exit(0)
            else:
                xzqz.execvp(args[0], args)
                xzqz._exit(1)
        else:
            ppppp.append(pid)
    for r, w in yyyyy:
        xzqz.close(r)
        xzqz.close(w)
    for pid in ppppp:
        xzqz.waitpid(pid, 0)


class QQAQ:
    def __init__(self, nbnq):
        self.nbnq = nbnq
        self.qzqq = None
        self.zqzz = 0
        self.nqpp = []
        self.zqzp = None

    def wqaq(self, pzpq, nznq):
        if pzpq != self.qzqq:
            self.zqzz = 0
            self.qzqq = pzpq
            self.zqzp = pzpq
            # Both builtins and executables in PATH
            path_env = xzqz.environ.get('PATH', '')
            all_execs = set(self.nbnq)
            for pdir in path_env.split(':'):
                if not pdir:
                    continue
                try:
                    for fname in xzqz.listdir(pdir):
                        fpath = xzqz.path.join(pdir, fname)
                        if xzqz.access(fpath, xzqz.X_OK) and not xzqz.path.isdir(fpath):
                            all_execs.add(fname)
                except Exception:
                    continue
            self.nqpp = sorted([qq for qq in all_execs if qq.startswith(pzpq)])

        if not self.nqpp:
            return None
        if len(self.nqpp) == 1:
            if nznq == 0:
                return self.nqpp[0] + ' '
            return None
        pppz = xzqz.path.commonprefix(self.nqpp)
        if len(pppz) > len(pzpq):
            if nznq == 0:
                return pppz
            return None
        if nznq == 0:
            self.zqzz += 1
            if self.zqzz == 1:
                qznq.stdout.write('\a')
                qznq.stdout.flush()
                return None
            elif self.zqzz == 2:
                qznq.stdout.write('\n' + '  '.join(self.nqpp) + '\n')
                qznq.stdout.write(f'$ {pzpq}')
                qznq.stdout.flush()
                return None
        return None


def pqpq(xpxp):
    for qzpz in ['2>>', '2>', '1>>', '1>', '>>', '>']:
        if qzpz in xpxp:
            return xpxp.split(qzpz, 1)[0].rstrip()
    return xpxp


def main():
    llll = []
    pppp = xzqz.getenv('HISTFILE')
    bbbb = 0
    if pppp and xzqz.path.exists(pppp):
        with open(pppp, 'r') as h:
            llll.extend([line.rstrip() for line in h if line.rstrip()])
        bbbb = len(llll)

    qqqq = ['exit', 'echo', 'type', 'pwd', 'cd', 'history']
    zzzz = QQAQ(qqqq)
    zzzz.nbnq = bqqw(qqqq)

    # REMOVE old dynamic_path scan since QQAQ now always loads PATH
    qwpz.clear_history()
    qwpz.set_completer(zzzz.wqaq)
    qwpz.parse_and_bind('tab: complete')
    qwpz.set_completer_delims(' \t\n')

    while True:
        zzzzq = None
        xxxxx = None
        ccccc = None

        ssss = input('$ ')
        sssss = bqqw(ssss)
        sssssss = xqwp(ssss).split(' ', 1)
        qqqqqq = xqwp(ssss, nbnb=True)
        iiiiii = qqqqqq[0] if qqqqqq else ""
        llll.append(sssss)

        ssss, zzzzq, xxxxx, ccccc = pqpp(ssss)

        if '|' in ssss:
            wwww([c.strip() for c in ssss.split('|')])
            continue

        if '2>>' in sssss:
            sss = sssss.split('2>>', 1)
            ddd = sss[0].strip()
            fff = sss[1].strip()
            if iiiiii in ['exit', 'echo', 'type', 'pwd', 'cd', 'history']:
                if iiiiii == 'echo':
                    with open(fff, 'a') as f:
                        pass
                    if len(sssssss) > 1:
                        print(pqpq(sssssss[1]))
                continue
            else:
                with open(fff, 'a') as f:
                    pqzq.run(ddd, shell=True, stderr=f)
                continue

        if '2>' in sssss:
            sss = sssss.split('2>', 1)
            ddd = sss[0].strip()
            fff = sss[1].strip()
            if iiiiii in ['exit', 'echo', 'type', 'pwd', 'cd', 'history']:
                if iiiiii == 'echo':
                    with open(fff, 'w') as f:
                        pass
                    if len(sssssss) > 1:
                        print(pqpq(sssssss[1]))
                continue
            else:
                with open(fff, 'w') as f:
                    pqzq.run(ddd, shell=True, stderr=f)
                continue

        if '1>>' in sssss or ('>>' in sssss and '1>>' not in sssss and '2>>' not in sssss):
            if '1>>' in sssss:
                sss = sssss.split('1>>')
            else:
                sss = sssss.split('>>')
            ddd = sss[0].strip()
            fff = sss[1].strip()
            with open(fff, 'a') as f:
                pqzq.run(ddd, shell=True, stdout=f)
            continue

        if '1>' in sssss or ('>' in sssss and '1>' not in sssss and '2>' not in sssss):
            if '1>' in sssss:
                sss = sssss.split('1>')
            else:
                sss = sssss.split('>')
            ddd = sss[0].strip()
            fff = sss[1].strip()
            with open(fff, 'w') as f:
                pqzq.run(ddd, shell=True, stdout=f)
            continue

        match iiiiii:
            case 'exit':
                if pppp:
                    with open(pppp, 'a') as h:
                        for line in llll[bbbb:]:
                            h.write(f'{line}\n')
                qznq.exit(int(sssssss[1]) if len(sssssss) > 1 else 0)

            case 'echo':
                if len(sssssss) > 1:
                    eeee = pqpq(sssssss[1])
                else:
                    eeee = ""
                if zzzzq:
                    if ccccc:
                        try:
                            open(zzzzq, 'r')
                        except FileNotFoundError:
                            azaz(zzzzq, '', xqaz=xxxxx)
                        finally:
                            azaz(zzzzq, '', xqaz=xxxxx)
                            print(eeee)
                    else:
                        azaz(zzzzq, eeee + '\n', xqaz=xxxxx)
                else:
                    print(eeee)

            case 'type':
                if len(sssssss) > 1:
                    nnnnnn = sssssss[1].strip()
                    if nnnnnn in qqqq:
                        print(f'{nnnnnn} is a shell builtin')
                    elif yyy := yqzn.which(nnnnnn):
                        print(f'{nnnnnn} is {yyy}')
                    else:
                        print(f'{nnnnnn}: not found')
                else:
                    print(f'{sssss}: not found')

            case 'pwd':
                print(xzqz.getcwd())

            case 'cd':
                try:
                    xzqz.chdir(nqpp.home() if sssssss[1] == '~' else sssssss[1])
                except:
                    print(f'cd: {sssssss[1]}: No such file or directory')

            case 'history':
                if len(sssssss) == 2:
                    if sssssss[1].startswith('-a'):
                        fff = sssssss[1][3:] if len(sssssss[1]) > 2 else pppp
                        if fff:
                            with open(fff, 'a') as h:
                                for line in llll[bbbb:]:
                                    h.write(f'{line}\n')
                            bbbb = len(llll)
                        continue
                    elif sssssss[1].startswith('-w'):
                        fff = sssssss[1][3:]
                        if fff:
                            with open(fff, 'w') as h:
                                for line in llll:
                                    h.write(f'{line}\n')
                            with open(fff, 'a') as h:
                                pass
                        continue
                    elif sssssss[1].startswith('-r'):
                        fff = sssssss[1][3:]
                        if fff and xzqz.path.exists(fff):
                            with open(fff, 'r') as h:
                                llll.extend([line.rstrip() for line in h if line.rstrip()])
                        continue

                hhh = llll
                if len(sssssss) == 2 and sssssss[1].isdigit():
                    lll = int(sssssss[1])
                    hhh = llll[-lll:]
                    nnn = len(llll) - len(hhh)
                else:
                    nnn = 0
                for x, line in enumerate(hhh):
                    print(f' {x + 1 + nnn} {line}')

            case _:
                if yqzn.which(iiiiii if iiiiii else ''):
                    try:
                        pqzq.run(qqqqqq)
                    except Exception as e:
                        print(e)
                else:
                    print(f'{ssss}: command not found')


if __name__ == '__main__':
    main()
