import glob
import os
from pathlib import Path
import sys

#STACK OPERATIONS

def load_index(code, value):
    code.emit("@"+value) 
    code.emit("D=A")    #Load index to memory

def push_base(code):      
    code.emit("@SP")
    code.emit("A=M")    #Top of the stack
    code.emit("M=D")    #Assign constant to address of stack pointer 
    code.emit("@SP")
    code.emit("M=M+1")  #Increment stack pointer

def find_address(code):
    code.emit("A=M+D")  #Find the value to push by calculating the base address + index      
    code.emit("D=M")

def op_push(args, code):
    memorysegment=args[0]
    value=args[1]

    match memorysegment:
        case "constant":
            load_index(code, value)
            push_base(code)
        case "local":
            load_index(code, value)
            code.emit("@LCL")   #Base address of LOCAL
            find_address(code)
            push_base(code)
        case "argument":
            load_index(code, value)
            code.emit("@ARG")   #Base address of ARGUMENT
            find_address(code)
            push_base(code)
        case "this":
            load_index(code, value)
            code.emit("@THIS")   #Base address of THIS
            find_address(code)
            push_base(code)
        case "that":
            load_index(code, value)
            code.emit("@THAT")   #Base address of THAT
            find_address(code)
            push_base(code)
        case "temp":
            load_index(code, value)
            code.emit("@5")   #Base address of TEMP
            code.emit("A=A+D")  #Find the value to push by calculating the base address + index      
            code.emit("D=M")
            push_base(code)
        case "pointer":
            match value:
                case "0":
                    code.emit("@THIS")   #Base address of THIS
                    code.emit("D=M")
                    push_base(code)
                case "1":
                    code.emit("@THAT")   #Base address of THAT
                    code.emit("D=M")
                    push_base(code)
        case "static":
            code.emit("@<FILENAME>."+value)   #Load address of static variable
            code.emit("D=M")
            push_base(code)
        case "_":
            raise Exception("Unknown memory segment"+memorysegment)
        
def pop_base(code):
    code.emit("@R13")   #Store target address in temporary general purpose register
    code.emit("M=D")
    code.emit("@SP")
    code.emit("AM=M-1") #Decrement SP and select address
    code.emit("D=M")    #Store top-most value in memory
    code.emit("@R13")
    code.emit("A=M")    #Pop to target address
    code.emit("M=D")

def store_top(code):
    code.emit("@SP")
    code.emit("AM=M-1") #Decrement SP and select address
    code.emit("D=M")    #Store top-most value in memory

def op_pop(args, code):
    memorysegment=args[0]
    value=args[1]

    match memorysegment:          
        case "local":
            load_index(code, value)
            code.emit("@LCL")   #Base address of LOCAL
            code.emit("D=M+D")  #Find the target address by calculating the base address + index
            pop_base(code)
        case "argument":
            load_index(code, value)
            code.emit("@ARG")   #Base address of ARGUMENT
            code.emit("D=M+D")  #Find the target address by calculating the base address + index
            pop_base(code)
        case "this":
            load_index(code, value)
            code.emit("@THIS")  #Base address of THIS
            code.emit("D=M+D")  #Find the target address by calculating the base address + index
            pop_base(code)
        case "that":
            load_index(code, value)
            code.emit("@THAT")  #Base address of THAT
            code.emit("D=M+D")  #Find the target address by calculating the base address + index
            pop_base(code)
        case "temp":
            load_index(code, value)
            code.emit("@5")     #Base address of TEMP
            code.emit("D=A+D")  #Find the target address by calculating the base address + index
            pop_base(code)
        case "pointer":
            match value:
                case "0":
                    store_top(code)
                    code.emit("@THIS")   #Base address of THIS
                    code.emit("M=D")
                case "1":
                    store_top(code)
                    code.emit("@THAT")   #Base address of THAT
                    code.emit("M=D")
        case "static":
            store_top(code)
            code.emit("@<FILENAME>."+value)   #Load address of static variable
            code.emit("M=D")
        case "_":
            raise Exception("Unknown memory segment"+memorysegment)
    pass

def log_arit_base(code):
    #Prepares the two top-most values of the stack for an operation

    code.emit("@SP")
    code.emit("AM=M-1")    #Choose address of top-most value on stack
    code.emit("D=M")      #Load top-most value to memory
    code.emit("A=A-1")    #Choose address of second top-most value

#ARITHMETICAL OPERATIONS

def op_add(code):
    log_arit_base(code)
    code.emit("M=D+M")    #Add values

def op_sub(code):
    log_arit_base(code)
    code.emit("M=M-D")    #Subtract top-most from second top

def op_neg(code):
    code.emit("@SP")
    code.emit("A=M-1")  #Choose address of top-most value on stack
    code.emit("M=-M")   #Negate value

#LOGICAL OPERATIONS

def op_eq(code):
    log_arit_base(code)
    code.new_label("EQUAL")
    code.new_label("END_EQ")
    code.emit("D=M_D")          #Subtract the two values (D = top - second_top)
    code.emit("@<EQUAL>")         #Jump to EQUAL if the result of subtraction is 0 (equal)
    code.emit("D;JEQ")

    code.emit("@SP")
    code.emit("A=M-1")          #Go to the location of second_top
    code.emit("M=0")            #Not equal, store 0 (false) in the second top position
    code.emit("@<END_EQ>")
    code.emit("0;JMP")          #Jump to the end to skip the 'equal' case

    code.emit("(<EQUAL>)")
    code.emit("@SP")
    code.emit("A=M-1")          #Go to the location of second_top
    code.emit("M=-1")           #Equal, store -1 (true) in the second top position

    code.emit("(<END_EQ>)")

def op_lt(code):
    log_arit_base(code)
    code.new_label("LESSTHAN")
    code.new_label("END_LT")
    code.emit("D=M-D")          #Subtract the two values (D = top - second_top)
    code.emit("@<LESSTHAN>")    #Jump to LESSTHAN if the result of subtraction is 0 (equal)
    code.emit("D;JLT")

    code.emit("@SP")
    code.emit("A=M-1")          #Go to the location of second_top
    code.emit("M=0")            #Not less than, store 0 (false) in the second top position
    code.emit("@<END_LT>")
    code.emit("0;JMP")          #Jump to the end to skip the 'equal' case

    code.emit("(<LESSTHAN>)")
    code.emit("@SP")
    code.emit("A=M-1")          #Go to the location of second_top
    code.emit("M=-1")           #Less than, store -1 (true) in the second top position

    code.emit("(<END_LT>)")

def op_gt(code):
    log_arit_base(code)
    code.new_label("GREATER")
    code.new_label("END_GT")
    code.emit("D=M-D")          #Subtract the two values (D = top - second_top)
    code.emit("@<GREATER>")     #Jump to GREATER if the result of subtraction is 0 (equal)
    code.emit("D;JGT")

    code.emit("@SP")
    code.emit("A=M-1")          #Go to the location of second_top
    code.emit("M=0")            #Not greater than, store 0 (false) in the second top position
    code.emit("@<END_GT>")
    code.emit("0;JMP")          #Jump to the end to skip the 'equal' case

    code.emit("(<GREATER>)")
    code.emit("@SP")
    code.emit("A=M-1")          #Go to the location of second_top
    code.emit("M=-1")           #Greater than, store -1 (true) in the second top position

    code.emit("(<END_GT>)")

def op_and(code):
    log_arit_base(code)
    code.emit("M=D&M")    #Perform bitwise AND on the values, and store the result in the second top position

def op_or(code):
    log_arit_base(code)
    code.emit("M=D|M")    #Perform bitwise OR on the values, and store the result in the second top position

def op_not(code):
    code.emit("@SP")
    code.emit("A=M-1")  #Choose address of top-most value on stack
    code.emit("M=!M")   #Perform bitwise NOT

#BRANCHING OPERATIONS

def op_label(args, code):
    label = args[0]
    code.emit('('+label+')')

def op_goto(args, code):
    label = args[0]         #The label to jump to
    code.emit("@"+label)    #Set jump address to the label
    code.emit("0;JMP")      #Jump to the label

def op_if_goto(args, code):
    label = args[0]         #The label to jump to if the condition is met
    store_top(code)
    code.emit("@"+label)    #Set jump address to the label
    code.emit("D;JNE")      #Jump to the label if the top value is not zero (False)

#FUNCTION CALL OPERATIONS

def op_function(args, code):
    function_name = args[0]
    num_variables = args[1]
    code.emit("("+function_name+")") 
    for i in range(int(num_variables)):
        op_push(["constant", "0"], code)

def op_call(args, code):
    function_name = args[0]
    num_variables = args[1]
    return_label = function_name+'$ret'
    code.new_label(return_label)
    #Push the return address
    code.emit("@<"+return_label+">")
    code.emit("D=A")
    push_base(code)
    #Push LCL
    code.emit("@LCL")
    code.emit("D=M")
    push_base(code)    
    #Push ARG
    code.emit("@ARG")
    code.emit("D=M")
    push_base(code)    
    #Push THIS
    code.emit("@THIS")
    code.emit("D=M")
    push_base(code)    
    #Push THAT
    code.emit("@THAT")
    code.emit("D=M")
    push_base(code)    
    #ARG = SP-5-num_variables
    code.emit("@SP")
    code.emit("D=M")
    code.emit("@5")
    code.emit("D=D-A")
    code.emit("@" + str(num_variables))
    code.emit("D=D-A")
    code.emit("@ARG")
    code.emit("M=D")   
    #LCL = SP
    code.emit("@SP")
    code.emit("D=M")
    code.emit("@LCL")
    code.emit("M=D")   
    #Goto functionName
    op_goto([function_name], code)    
    #(return_label)
    code.emit("(<"+return_label+">)")

def return_pointer_calc(code):
    #Find pointers for return
    for i in range(1,5):
        code.emit("@R13")
        code.emit("D=M")
        code.emit("@"+str(i))
        code.emit("A=D-A")
        code.emit("D=M")
        match i:
            case 1:
                code.emit("@THAT")
            case 2:
                code.emit("@THIS")
            case 3:
                code.emit("@ARG")
            case 4:
                code.emit("@LCL")
        code.emit("M=D") 

def op_return(code):
    #endFrame = LCL
    code.emit("@LCL")
    code.emit("D=M")
    code.emit("@R13")  #R13 holds the endFrame
    code.emit("M=D")   
    #retAddr = *(endFrame - 5)
    code.emit("@5")
    code.emit("D=A")
    code.emit("@R13")
    code.emit("A=M-D")
    code.emit("D=M")
    code.emit("@R14")  #R14 holds the return address
    code.emit("M=D")   
    #*ARG = pop()
    code.emit("@SP")
    code.emit("AM=M-1")
    code.emit("D=M")
    code.emit("@ARG")
    code.emit("A=M")
    code.emit("M=D")    
    #SP = ARG + 1
    code.emit("@ARG")
    code.emit("D=M+1")
    code.emit("@SP")
    code.emit("M=D")   
    #THAT = *(endFrame - 1), THIS = *(endFrame - 2), ARG = *(endFrame - 3), LCL = *(endFrame - 4)
    return_pointer_calc(code)
    #goto retAddr
    code.emit("@R14")
    code.emit("A=M")
    code.emit("0;JMP")

def assembler(ifn: str, code_obj):
    with open(ifn, "r") as input_file:
        for line in input_file:
            words = line.split()  #Split line into words
            if len(words) == 0:   #Skip empty lines
                continue            
            op = words[0]
            args = words[1:]
            if op == ("//"):
                continue

            match op:
                case 'push':
                    op_push(args, code_obj)
                case 'pop':
                    op_pop(args, code_obj)
                case 'add':
                    op_add(code_obj)
                case 'sub':
                    op_sub(code_obj)
                case 'neg':
                    op_neg(code_obj)
                case 'eq':
                    op_eq(code_obj)
                case 'lt':
                    op_lt(code_obj)
                case 'gt':
                    op_gt(code_obj)
                case 'and':
                    op_and(code_obj)
                case 'or':
                    op_or(code_obj)
                case 'not':
                    op_not(code_obj)
                case 'label':
                    op_label(args, code_obj)
                case 'goto':
                    op_goto(args, code_obj)
                case 'if-goto':
                    op_if_goto(args, code_obj)
                case 'function':
                    op_function(args, code_obj)
                case 'call':
                    op_call(args, code_obj)
                case 'return':
                    op_return(code_obj)
                case _:
                    raise Exception("Unexpected operation " + op)

class Code:
    def __init__(self, output_file_name):
        self.ofn = output_file_name
        self.labels = {}
        self.ofd = open(output_file_name, "w")
        self.base_fn = "bootstrap"

    def set_input_file(self, fn):
        self.base_fn = Path(fn).stem

    def new_label(self, label):
        if label in self.labels:
            self.labels[label] = self.labels[label] + 1
        else:
            self.labels[label] = 1

    def replace_labels(self, s):
        for label in self.labels:
            # replace <LABEL> to LABEL1 (or LABEL2, LABEL3...)
            s = s.replace("<" + label + ">", label + str(self.labels[label]))
        s = s.replace("<FILENAME>", self.base_fn)
        return s

    def emit(self, s):
        s = self.replace_labels(s)
        self.ofd.write(s)
        self.ofd.write("\n")

    def emit_comment(self, comment):
        comment = self.replace_labels(comment)
        self.ofd.write("// ")
        self.ofd.write(comment)
        if comment[-1] != "\n":
            self.ofd.write("\n")

    def close(self):
        self.ofd.close()

    def __exit__(self, *args):
        self.close()

def bootstrapcode(code):
    #Set SP = 256 (initialize the stack pointer)
    code.emit("@256")
    code.emit("D=A")
    code.emit("@SP")
    code.emit("M=D")   
    #Set LCL = 300 (initialize the local segment)
    code.emit("@300")
    code.emit("D=A")
    code.emit("@LCL")
    code.emit("M=D")   
    #Set ARG = 400 (initialize the argument segment)
    code.emit("@400")
    code.emit("D=A")
    code.emit("@ARG")
    code.emit("M=D")    
    #Set THIS = 3000 (initialize the this segment)
    code.emit("@3000")
    code.emit("D=A")
    code.emit("@THIS")
    code.emit("M=D")  
    #Set THAT = 3010 (initialize the that segment)
    code.emit("@3010")
    code.emit("D=A")
    code.emit("@THAT")
    code.emit("M=D")
    #Call Sys.init function
    op_call(['Sys.init', '0'], code)  #Call with 0 arguments

def process_directory(input_directory):
    # output file name
    output_filename = input_directory + os.sep + input_directory.split(os.sep)[-1] + ".asm"
    print("Input directory:", input_directory)
    print("Output assembler file:", output_filename)

    # new code generator object
    code = Code(output_filename)

    # bootstrap code
    for filename in glob.glob(input_directory + os.sep + "*.vm"):
        basename = filename.split(os.sep)[-1]
        if basename.lower() == "sys.vm":
            # we generate the bootstrap code if
            # there is a file named sys.vm in the directory
            bootstrapcode(code)
            break

    # process all .vm files in directory
    for input_filename in glob.glob(input_directory + os.sep + "*.vm"):
        print("Generating asm code from " + input_filename, "to", output_filename)
        code.set_input_file(input_filename)
        assembler(input_filename, code)

    code.close()

if __name__ == "__main__":
        input_directory = sys.argv[1]
        process_directory(input_directory)