; ============================================================================
; VALID FULL CPU8/16 TEST PROGRAM
; Exercises every mnemonic from table.csv at least once.
; Clean flow, ends with ret + hlt.
; ============================================================================

.text
.global _start

_start:
main:
    nop
    inte
    intd

    ldi ac, 0x01
    ldi xh, 0x02
    ldi yl, 0x03
    ldi yh, 0x04
    ldi fr, 0x05
    ldi zl, 0x06
    ldi zh, 0x07

    ldi x,  0x1111
    ldi y,  0x2222
    ldi z,  0x3333
    ldi sp, 0x4444

    ld ac, [ro_data]
    ld xh, [ro_data]
    ld yl, [ro_data]
    ld yh, [ro_data]
    ld fr, [ro_data]
    ld zl, [ro_data]
    ld zh, [ro_data]

    st [rw_data], ac
    st [rw_data], xh
    st [rw_data], yl
    st [rw_data], yh
    st [rw_data], fr
    st [rw_data], zl
    st [rw_data], zh

    push ac
    push xh
    push yl
    push yh
    push fr
    push zl
    push zh
    push x
    push y
    push z
    push pc

    pop ac
    pop xh
    pop yl
    pop yh
    pop fr
    pop zl
    pop zh
    pop x
    pop y
    pop z

    mov ac, xh
    mov xh, ac
    mov yl, ac
    mov yh, ac
    mov fr, ac
    mov zl, ac
    mov zh, ac
    mov ac, yl
    mov ac, yh
    mov ac, fr
    mov ac, zl
    mov ac, zh
    mov xh, yl
    mov yh, fr
    mov zh, zl
    mov sp, z
    mov z, sp
    mov z, pc

    add ac
    add xh
    add yl
    add yh
    add zl
    add zh
    addi 0x11

    sub ac
    sub xh
    sub yl
    sub yh
    sub zl
    sub zh
    subi 0x22

    nand ac
    nand xh
    nand yl
    nand yh
    nand zl
    nand zh
    nandi 0x33

    xor ac
    xor xh
    xor yl
    xor yh
    xor zl
    xor zh
    xori 0x44

    nor ac
    nor xh
    nor yl
    nor yh
    nor zl
    nor zh
    nori 0x55

    adc ac
    adc xh
    adc yl
    adc yh
    adc zl
    adc zh
    adci 0x66

    sbb ac
    sbb xh
    sbb yl
    sbb yh
    sbb zl
    sbb zh
    sbbi 0x77

    inc ac
    inc xh
    inc yl
    inc yh
    inc zl
    inc zh

    dec ac
    dec xh
    dec yl
    dec yh
    dec zl
    dec zh

    icc ac
    icc xh
    icc yl
    icc yh
    icc zl
    icc zh

    dcb ac
    dcb xh
    dcb yl
    dcb yh
    dcb zl
    dcb zh

    not ac
    not xh
    not yl
    not yh
    not zl
    not zh

    cmp ac
    cmp xh
    cmp yl
    cmp yh
    cmp zl
    cmp zh
    cmpi 0x12

    shl
    shr

    jnz next1
    jnzx
    jz next1
    jzx
    jnc next1
    jncx
    jc next1
    jcx
    jp next1
    jpx
    jm next1
    jmx
    jmp next1 00 00
    jmpx

next1:
    cnz sub1
    cz sub1
    cnc sub1
    cc sub1
    cp sub1
    cm sub1
    call sub1

    rnz
    rz
    rnc
    rc
    rp
    rm

    call exit
    hlt
sub1:
    addi 0xAA
    ret

exit:
    ret

.rodata
ro_data:
    .byte 0x11, 0x22

.bss
rw_data:
    .res 4
