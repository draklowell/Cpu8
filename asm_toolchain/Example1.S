# 1 "../Example.S"
# 1 "<built-in>" 1
# 1 "<built-in>" 3
# 467 "<built-in>" 3
# 1 "<command line>" 1
# 1 "<built-in>" 2
# 1 "../Example.S" 2



.text
main:
  ldi sp, 0xffff
  ldi yl, 13
  ldi yh, 67
  mov ac, yl

  ld ac, [data]
  intd
  shl
  inte

  ldi zl, data
  shr
  ld zl, [n]
  call test
  hlt

test:
  ldi ac, 0xff
  ret

.bss
n:
  .res 5

.rodata
data:
  .byte 13
