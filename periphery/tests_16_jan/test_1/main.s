.global main
.text
main:
    ldi sp, 0xFFFE
    ldi ac, 99
    ldi xh, 1
    add xh
    st [res], ac
    hlt

.rodata
res:
    .word 0x2000