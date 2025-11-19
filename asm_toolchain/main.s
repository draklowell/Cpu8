
.global main
.extern sum
.text
main:
    ldi sp, 0xFFFE
    ld ac, [num1]
    ld zh, [num2]
    call sum
    hlt


.rodata
num1:
    .byte 12
num2:
    .byte 8
