#include "sum.inc"
#define ONE 1
#define TWO 2
.global main
.text
main:
    ld ac, [one]
    ld zh, [two]
    call sum
    hlt


.rodata
one:
    .byte ONE
two:
    .byte TWO
