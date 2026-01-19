.global main
.text
main:
    nop
    ldi ac, 100
    inc ac
    st [label], ac
    nop
    hlt



.bss
label:
    .res 1