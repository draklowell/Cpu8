.global main
.text
main:
    st [res1], zh
    st [res2], ac
    st [res3], yl
    st [res4], xh
    st [res5], yh
    hlt
.rodata
res1:
    .word 0x1000
res2:
    .word 0x2000
res3:
    .word 0x3000
res4:
    .word 0x4000
res5:
    .word 0x5000