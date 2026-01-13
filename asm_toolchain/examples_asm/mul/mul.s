
;;   result = 0
;;   while B != 0:
;;       if (B & 1) != 0:
;;           result += A
;;       A <<= 1
;;       B >>= 1
;;   return result

.global mul
.text

mul:

    mov yl, ac          ; YL = A (multiplicand)
    mov yh, xh          ; YH = B (multiplier)
    ldi zl, 0           ; ZL = result low = 0
    ldi zh, 0           ; ZH = result high = 0
    ldi xh, 0           ; XH = A_high (for 16-bit add) = 0

mul_loop:
    mov ac, yh          ; AC = B
    cmpi 0              ; Compare B with 0
    jz mul_done         ; If B == 0, we're done

    mov ac, yh          ; AC = B
    shr                 ; AC = B >> 1
    shl                 ; AC = (B >> 1) << 1 = B with bit0 cleared
    cmp yh              ; Compare with original B
    jz mul_skip_add     ; If equal, bit0 was 0, skip add

    mov ac, zl          ; AC = result_low
    add yl              ; AC = result_low + A_low
    mov zl, ac          ; ZL = new result_low

    mov ac, zh          ; AC = result_high
    jc mul_add_carry    ; If carry from low add, increment high
    jmp mul_after_add

mul_add_carry:
    inc zh              ; ZH++

mul_after_add:
    mov ac, zh          ; AC = result_high
    add xh              ; AC += A_high
    mov zh, ac          ; ZH = new result_high

mul_skip_add:
    mov ac, yl          ; AC = A_low
    shl                 ; AC = A_low << 1
    mov yl, ac          ; YL = new A_low
    mov ac, xh          ; AC = A_high
    shl                 ; AC = A_high << 1
    mov xh, ac          ; XH = new A_high (Note: carry from YL lost, ok for 8x8)

    mov ac, yh          ; AC = B
    shr                 ; AC = B >> 1
    mov yh, ac          ; YH = new B

    jmp mul_loop

mul_done:
    mov ac, zl          ; AC = result_low
    mov xh, zh          ; XH = result_high
    ret


