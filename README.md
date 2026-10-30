# zeroguard.py

Does your build have a safety check that a zero walks straight through?

`#ifndef X` only asks whether `X` is defined. If `X` is defined as `0` (`#define X 0`, `#define X (0)`, or `-DX=0` in a build
file), the check passes even though the setting says "off". `zeroguard.py` finds every `#ifdef`, `#ifndef` and `defined()`
check on a macro that's defined as zero anywhere in the tree.

```
./zeroguard.py src/ lib/
```

On the two real files behind the Coldcard seed bug (libngu at `cf1988a`, Coldcard firmware at `b18723d`, March 2021):

```
./random.c:28: `# ifndef MICROPY_HW_ENABLE_RNG` only tests that MICROPY_HW_ENABLE_RNG exists
    MICROPY_HW_ENABLE_RNG is defined as 0 at ./mpconfigboard.h:77: `#define MICROPY_HW_ENABLE_RNG       (0)`
zeroguard: 1 check(s) on zero-defined macros
```

The library's guard was `# error "get a HW TRNG plz"`: refuse to build without a hardware random number generator. The board
config, under the comment `// We have our own version of this code.`, set `MICROPY_HW_ENABLE_RNG` to `(0)`. In MicroPython,
0 means "no hardware RNG: build the software fallback", which had the same function name, so it linked. Seeds were generated
from that fallback from March 2021 until the July 2026 fix. Coinkite: "I explicitly set MICROPY_HW_ENABLE_RNG to zero,
thinking we didn't need either version, but that's not what it does."

Exit 0 means nothing found, 1 means at least one finding, 2 means usage. Python 3, no dependencies. A finding isn't always a
bug: some code really does mean "defined at all". Read each one. It doesn't evaluate macros or follow includes, so a zero
that arrives through another macro won't be seen.

The fix for the bug itself is the other half: check what actually got linked. Coldcard's fix fails the build if the wrong
`rng_get` ends up in the binary.

Sources: https://blog.coinkite.com/entropy-technical-backgrounder/ ·
https://github.com/switck/libngu/blob/cf1988aa54969a7d2dcef261ee664a41a7013262/ngu/random.c#L22-L31 ·
https://github.com/Coldcard/firmware/blob/b18723dddb6d751c39978e4364b56b2414f68b47/stm32/COLDCARD/mpconfigboard.h#L76-L77
