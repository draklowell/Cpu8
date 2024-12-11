mvd r3, a
iop 0, r3
mvr r5, r3
iop 1, r5
mvd r0, 2
sub r3, r0
mva r0, r3 
mvf r1, r0
iop 0, r1
add r1, r0 
mvd r2, 1
sub r0, r2
add r3, r0
iop 1, r3
mvd r7, 9
mvd r6, f
nand r7, r6
iop 0, r7
mvd r0, 2
mvd r1, 2
sub r0, r1
jeq test1
continue1:
    sub r3, r4
    jeq test1
jls test2
continue2:
    mvd r0, 1
    mvd r1, 1
    sub r0, r1
    jls test2
    jle test3
continue3:
    sub r0, r1
    jle jump_test4
cont4:
    sub r5, r6
    jle jump_test4
jne jump_test5
test1:
    mvd r3, 2
    mvd r4, f
    jeq continue1
test2:
    mvd r3, 5
    mvd r4, 6
    jls continue2
test3:
    mvd r0, 2    
    mvd r1, 3
    jle continue3
jump_test4:
    mvd r5, 5
    mvd r6, 3
    jle cont4
jump_test5:
    mvd r2, 3
    mvd r1, c
    mvd r1, 0
    mvd r2, 0
    mvd r1, d
    mvd r1, 0
    mvd r2, 5
    mvd r1, d
    mvd r1, 0
    mvd r2, 0
    mvd r1, a
    mvd r2, 5
    sub r1, r2
    jeq jump_test5

interrupt_code:
    io_int
    mvd r6, f
    mvf r7, r6 
    iop 0, r7
    ret

