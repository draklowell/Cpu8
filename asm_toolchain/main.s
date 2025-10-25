.extern sum
.global main
.text
main:
    ld ac, [one]
    ld zh, [two]
    call sum
    hlt


.rodata
one:
    .byte 1
two:
    .byte 2
