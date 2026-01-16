.global main
.text
main:
    ldi yl, 10
    mov ac, yl
    inc ac
    st [res], ac
    hlt


.rodata
res:
    .word 0x2000