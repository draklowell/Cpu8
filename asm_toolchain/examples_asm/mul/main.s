.global main
.extern mul
.text
main:
    ld ac, [input1]
    ld xh, [input2]
    call mul
    hlt

.rodata
input1:
    .byte 15
input2:
    .byte 2
