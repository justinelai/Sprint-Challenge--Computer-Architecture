"""CPU functionality."""

import sys


POP = 0b01000110
PUSH= 0b01000101

# Sets PC
CALL= 0b01010000
RET = 0b00010001
JMP = 0b01010100 
JNE = 0b01010110
JEQ = 0b01010101 

#ALU
ADD = 0b10100000
MUL = 0b10100010
CMP = 0b10100111

HLT = 0b00000001
LDI = 0b10000010
PRN = 0b01000111

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.register = [0] * 8
        self.memory = [0] * 256 #256 bytes of memory
        self.pc = 0 # Program Counter, address of the currently executing instruction
        self.fl = 0 # Flag
        self.branchtable = {}
        self.branchtable[HLT] = self.handle_hlt
        self.branchtable[LDI] = self.handle_ldi
        self.branchtable[PRN] = self.handle_prn
        self.branchtable[MUL] = self.handle_mul
        self.branchtable[ADD] = self.handle_add
        self.branchtable[CMP] = self.handle_cmp
        
        self.branchtable[PUSH] = self.push
        self.branchtable[POP] = self.pop
        self.branchtable[CALL] = self.call
        self.branchtable[RET] = self.ret
        self.branchtable[JMP] = self.jmp
        self.branchtable[JNE] = self.jne
        self.branchtable[JEQ] = self.jeq

        self.sp = 7
        self.register[self.sp] = 0xf4 # initialize stack pointer to empty stack

    def push(self, operands):
        self.register[self.sp] -= 1 #decrement sp
        reg_num = self.memory[self.pc + 1]
        reg_value = self.register[reg_num]
        self.memory[self.register[self.sp]] = reg_value # copy register value into memory at address SP
        self.pc += 2

    def pop(self, operands):
        val = self.memory[self.register[self.sp]]
        reg_num = self.memory[self.pc + 1]
        self.register[reg_num] = val # copy val FROM memory at SP into register
        self.register[self.sp] += 1
        self.pc += 2
        
    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        """
        Compare the values in two registers.
        If they are equal, set the Equal E flag to 1, otherwise set it to 0.
        If registerA is less than registerB, set the Less-than L flag to 1, otherwise set it to 0.
        If registerA is greater than registerB, set the Greater-than G flag to 1, otherwise set it to 0.
        """

        if op == "ADD":
            self.register[reg_a] += self.register[reg_b]
        elif op == "MUL":
            self.register[reg_a] *= self.register[reg_b]
        elif op == "CMP":
            if self.register[reg_a] == self.register[reg_b]:
                self.fl = 0b00000001
            elif self.register[reg_a] < self.register[reg_b]:
                self.fl = 0b00000100
            elif self.register[reg_a] > self.register[reg_b]:
                self.fl = 0b00000010
            else: 
                raise Exception("Unsupported ALU operation") 
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.register[i], end='')

        print()

    def ram_read(self, address):
        # should accept the address to read and return the value stored there.
        return self.memory[address]
       
    def ram_write(self, address, value):
        # should accept a value to write, and the address to write it to.
        self.memory[address] = value

    def run(self):
        """Run the CPU."""
        print("Running CPU...")
        running = True
        while running:
            ir = self.ram_read(self.pc)
            operand_count = (ir >> 6) & 0b00000011
            #pc_setter = (ir >> 4) & 0b00000001
            operands = []
            for i in range(1, operand_count + 1):
                operands.append(self.ram_read(self.pc + i))
            if ir in self.branchtable:
                self.branchtable[ir](operands)
            else:
                print("Instruction not found!")

    def handle_hlt(self, operands):
        print("Halted!")
        self.running = False
        sys.exit(1) # Error exit status
    def handle_ldi(self, operands):
        # LDI register immediate - Set the value of a register to an integer.
        self.register[operands[0]] = operands[1]
        self.pc += 3
    def handle_prn(self, operands):
        # PRN register pseudo-instruction - Print numeric value stored in the given register.
        # Print to the console the decimal integer value that is stored in the given register.
        print(self.register[operands[0]])
        self.pc += 2

    def handle_mul(self, operands):
        self.alu("MUL", operands[0], operands[1])
        self.pc += 3
    def handle_add(self, operands):
        self.alu("ADD", operands[0], operands[1])
        self.pc += 3
    def handle_cmp(self, operands):
        self.alu("CMP", operands[0], operands[1])
        self.pc += 3

    def call(self, operands):
        #push return addr on stack
        self.register[self.sp] -= 1 #decrement sp
        self.memory[self.register[self.sp]] = self.pc + 2
        # set pc to value in register
        reg_num = self.memory[self.pc + 1]
        self.pc = self.register[reg_num] # setting PC directly - DON'T increment to next automatically
    
    def ret(self, operands):
        # pop return addr off stack, store it in the pc
        self.pc = self.memory[self.register[self.sp]]
        self.register[self.sp] += 1

    def jmp(self, operands):
        # Jump to the address stored in the given register. Set the PC to the address stored in the given register.
        self.pc = self.register[operands[0]]
    
    def jne(self, operands):
        #If E flag is clear (false, 0), jump to the address stored in the given register.
        if (self.fl & 0b00000001) is 0:
            self.pc = self.register[operands[0]]
        else:
            self.pc += 2

    def jeq(self, operands):
        #If equal flag is set (true), jump to the address stored in the given register.
        if (self.fl & 0b00000001) is 1:
            self.pc = self.register[operands[0]]
        else:
            self.pc += 2

    def load(self):
        if len(sys.argv) != 2:
            print("Usage: file.py filename", file=sys.stderr)
            sys.exit(1)
        try:
            address = 0

            with open(sys.argv[1]) as f:
                for line in f:
                    # Ignore comments
                    comment_split = line.split("#")
                    num = comment_split[0].strip()
                    if num == "":
                        continue  # Ignore blank lines
                    value = int(num, 2)   # Base 10, but ls-8 is base 2
                    self.memory[address] = value
                    address += 1
        except FileNotFoundError:
            print(f"{sys.argv[0]}: {sys.argv[1]} not found")
            sys.exit(2)