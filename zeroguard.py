#!/usr/bin/env python3
"""zeroguard.py: find #ifdef / #ifndef / defined() checks on macros that are defined as 0.

  ./zeroguard.py <dir-or-file>...

`#ifndef X` only asks whether X is defined. If X is defined as 0 somewhere (#define X 0, #define X (0), or -DX=0 in a
build file), the check passes even though the setting says "off". That's how a Coldcard safety check ("no hardware RNG?
refuse to build") let firmware link a software fallback for five years.

Exit 0 nothing found, 1 at least one check on a zero-defined macro, 2 usage.
"""
import os, re, sys

SRC = (".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".ino", ".m", ".mm")
BUILD = ("makefile", "gnumakefile", "cmakelists.txt", "meson.build", "sconstruct", "sconscript", "build.ninja")
BUILD_EXT = (".mk", ".cmake", ".mak", ".bzl", ".bazel", ".gyp", ".gypi")
ZERO = r"\(?\s*(?:0+|0[xX]0+)[uUlL]*\s*\)?"
DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s+" + ZERO + r"\s*(?:$|//|/\*)")
FLAG = re.compile(r"-D\s*([A-Za-z_]\w*)=" + ZERO + r"(?=[\s'\"]|$)")
CHECK = re.compile(r"^\s*#\s*(?:(ifn?def)\s+([A-Za-z_]\w*)|(?:el)?if\b(.*))")
DEFINED = re.compile(r"(!?)\s*defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?")

def files(paths):
    for p in paths:
        if os.path.isfile(p): yield p; continue
        for root, dirs, names in os.walk(p):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "build")]
            for n in names:
                low = n.lower()
                if low.endswith(SRC) or low in BUILD or low.endswith(BUILD_EXT): yield os.path.join(root, n)

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip().split("\n\n")[0] + "\n\n  ./zeroguard.py <dir-or-file>...", file=sys.stderr); return 2
    if not all(os.path.exists(p) for p in argv):
        print("zeroguard: no such path: " + ", ".join(p for p in argv if not os.path.exists(p)), file=sys.stderr); return 2
    zero, checks = {}, []
    for f in files(argv):
        try: lines = open(f, errors="replace").read().split("\n")
        except OSError: continue
        src = f.lower().endswith(SRC)
        for n, line in enumerate(lines, 1):
            if src:
                m = DEFINE.match(line)
                if m: zero.setdefault(m.group(1), []).append((f, n, line.strip()))
                m = CHECK.match(line)
                if m:
                    if m.group(1): checks.append((f, n, line.strip(), m.group(2)))
                    else:
                        for _, name in DEFINED.findall(m.group(3) or ""): checks.append((f, n, line.strip(), name))
            for name in FLAG.findall(line):
                zero.setdefault(name, []).append((f, n, "-D%s=0" % name))
    hits = [(f, n, text, name) for f, n, text, name in checks if name in zero]
    for f, n, text, name in hits:
        df, dn, dtext = zero[name][0]
        more = f" (and {len(zero[name]) - 1} more)" if len(zero[name]) > 1 else ""
        print(f"{f}:{n}: `{text}` only tests that {name} exists")
        print(f"    {name} is defined as 0 at {df}:{dn}: `{dtext}`{more}")
    print(f"zeroguard: {len(hits)} check(s) on zero-defined macros" if hits else "zeroguard: none found")
    return 1 if hits else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
