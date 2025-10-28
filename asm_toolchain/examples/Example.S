#define NUMBER 13
#define ALLNUMBER 67
.global main
.text
main:
  ldi sp, 0xffff
  ldi yl, NUMBER
  ldi yh, ALLNUMBER
  mov ac, yl

  ld  ac, [data]
  intd
  shl
  inte

  ldi z, data
  shr
  ld z, [n]
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