.global main
.text
main:
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    inc ac
    jmp test_label
    hlt


test_label:
    subi 16
    st [res], ac
    hlt

.rodata
res:
    .word 0x1000
