.text
main:
  ldi y, 0x1223
  ldi yl, 13
  ldi yh, 31
  ld ac, [data]
  intd
  shl
  inte

  ldi z, data
  shr

  call test
  hlt

test:
  ldi ac, 0x88
  ret

.rodata
data:
  .byte 0x01
