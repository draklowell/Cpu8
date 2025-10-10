.text
main:
  ldi sp, 0xffff
  ldi yl, 13
  ldi yh, 31
  mov ac, yl
  add yh

  ld  ac, [data]
  intd
  shl
  inte

  ldi z, data
  stx ac
  shr

  call test
  hlt

test:
  ldi ac, 0xff
  ret

.data
data:
  .byte 0x01
