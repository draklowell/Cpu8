; Auto-generated sample exercising all instruction mnemonics from table.csv
.text
.global main
main:
    nop
    inte
    intd
    ldi ac, 0x12
    ld ac, [load_word]
    ldi xh, 0x12
    ld xh, [load_word]
    ldi yl, 0x12
    ld yl, [load_word]
    ldi yh, 0x12
    ld yh, [load_word]
    ldi fr, 0x12
    ld fr, [load_word]
    ldi zl, 0x12
    ld zl, [load_word]
    ldi zh, 0x12
    ld zh, [load_word]
    ldi x, 0x1234
    ldi y, 0x1234
    ldi z, 0x1234
    ldi sp, 0x1234
    ldx ac
    ldx xh
    ldx yl
    ldx yh
    ldx fr
    st [store_word], ac
    st [store_word], xh
    inth
    st [store_word], yl
    st [store_word], yh
    st [store_word], fr
    st [store_word], zl
    st [store_word], zh
    stx ac
    stx xh
    stx yl
    stx yh
    stx fr
    mov xh, ac
    mov yl, ac
    mov yh, ac
    mov fr, ac
    mov zl, ac
    mov zh, ac
    mov ac, xh
    mov yl, xh
    mov yh, xh
    mov fr, xh
    mov zl, xh
    mov zh, xh
    mov ac, yl
    mov xh, yl
    mov yh, yl
    mov fr, yl
    mov zl, yl
    mov zh, yl
    mov ac, yh
    mov xh, yh
    mov yl, yh
    mov fr, yh
    mov zl, yh
    mov zh, yh
    mov ac, fr
    mov xh, fr
    mov yl, fr
    mov yh, fr
    mov zl, fr
    mov zh, fr
    mov ac, zl
    mov xh, zl
    mov yl, zl
    mov yh, zl
    mov fr, zl
    mov zh, zl
    mov ac, zh
    mov xh, zh
    mov yl, zh
    mov yh, zh
    mov fr, zh
    mov zl, zh
    mov sp, z
    mov z, sp
    mov z, pc
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
    jnz branch_target
    jnzx
    jz branch_target
    jzx
    jnc branch_target
    jncx
    jc branch_target
    jcx
    jp branch_target
    jpx
    jm branch_target
    jmx
    jmp branch_target
    jmpx
    cnz call_target
    cz call_target
    cnc call_target
    cc call_target
    cp call_target
    cm call_target
    call call_target
    rnz
    rz
    rnc
    rc
    rp
    rm
    ret
    add ac
    add xh
    add yl
    add yh
    add zl
    add zh
    addi 0x12
    sub ac
    sub xh
    sub yl
    sub yh
    sub zl
    sub zh
    subi 0x12
    nand ac
    nand xh
    nand yl
    nand yh
    nand zl
    nand zh
    nandi 0x12
    xor ac
    xor xh
    xor yl
    xor yh
    xor zl
    xor zh
    xori 0x12
    nor ac
    nor xh
    nor yl
    nor yh
    nor zl
    nor zh
    nori 0x12
    adc ac
    adc xh
    adc yl
    adc yh
    adc zl
    adc zh
    adci 0x12
    sbb ac
    sbb xh
    sbb yl
    sbb yh
    sbb zl
    sbb zh
    sbbi 0x12
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
    hlt
branch_target:
    nop
call_target:
    ret

.rodata
load_word:
    .word 0x1234

.bss
store_word:
    .res 2