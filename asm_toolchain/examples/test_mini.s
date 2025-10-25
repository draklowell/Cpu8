
.rodata
number:
    .byte 0x12

data:
    .byte 0x15

.global main
.text
main:
    push ac
    ld zl, [number]

    ld xl, [number]
    hlt
