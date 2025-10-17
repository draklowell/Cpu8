.text
main:
  ldi sp, 0xffff
  ldi yl, 13
  ldi yh, 31
  mov ac, yl

  ld  ac, [data]
  intd
  shl
  inte

  ldi z, data
  shr
  ldi z, [n]
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
  .byte 0x01