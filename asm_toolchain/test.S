#include <test2.S>

main:
  ldi xh 0xff
#ifdef LINUX
  linuxprint xh
#else
  windowsprint xh
#endif
  jmp print
  hlt
