.global main
.text
main:
    ld ac, [test_label]
    st [res], ac
    hlt


test_label:
    .byte 0x66

.rodata
res:
    .word 0x1000