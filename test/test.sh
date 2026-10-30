#!/bin/sh
# sh test/test.sh: checks zeroguard.py on small source trees built here. No network.
cd "$(dirname "$0")/.." || exit 1
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
fail=0
check() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }
Z="python3 -I $PWD/zeroguard.py"

mkdir "$T/a"; printf '#define HAVE_RNG (0)\n' > "$T/a/cfg.h"; printf '#ifndef HAVE_RNG\n#error no rng\n#endif\n' > "$T/a/r.c"
out=$($Z "$T/a"); code=$?
check "#ifndef on a macro defined as (0) is found" '[ $code -eq 1 ] && echo "$out" | grep -q "r.c:1"'

mkdir "$T/b"; printf '#define HAVE_RNG 1\n' > "$T/b/cfg.h"; printf '#ifndef HAVE_RNG\n#error\n#endif\n' > "$T/b/r.c"
$Z "$T/b" >/dev/null; code=$?
check "a macro defined as 1 is fine" '[ $code -eq 0 ]'

mkdir "$T/c"; printf 'CFLAGS += -DUSE_HW=0\n' > "$T/c/Makefile"; printf '#if defined(USE_HW) && X\n#endif\n' > "$T/c/m.c"
out=$($Z "$T/c"); code=$?
check "#if defined() with -DX=0 in a Makefile is found" '[ $code -eq 1 ] && echo "$out" | grep -q "Makefile"'

mkdir "$T/d"; printf '#define HAVE_RNG 0\n#if HAVE_RNG\n#endif\n' > "$T/d/v.c"
$Z "$T/d" >/dev/null; code=$?
check "#if X (a value test) is not flagged" '[ $code -eq 0 ]'

mkdir "$T/e"; printf '#define FLAG 0x0u // off\n#ifdef FLAG\n#endif\n' > "$T/e/h.h"
$Z "$T/e" >/dev/null; code=$?
check "0x0u with a trailing comment counts as zero" '[ $code -eq 1 ]'

$Z >/dev/null 2>&1; code=$?
check "no arguments is a usage error" '[ $code -eq 2 ]'
$Z "$T/nope" >/dev/null 2>&1; code=$?
check "a missing path is a usage error" '[ $code -eq 2 ]'
exit $fail
