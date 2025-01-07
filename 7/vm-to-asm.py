import sys

class Code:
    def __init__(self, fn):
        # Constructor initializes the Code class with the file name `fn`.
        # It stores the file name and base name (file name without extension)
        # and opens a file for writing.
        
        self.fn = fn  # Store the file name.
        
        # If the file has an extension (".xxx"), extract the base file name.
        if fn[-4] == ".":
            self.base_fn = fn[:-4]  # Strip the last 4 characters (e.g., '.txt').
        else:
            self.base_fn = fn  # Use the full name if there's no recognized extension.
        
        self.labels = {}  # Dictionary to track the occurrence count of labels.
        self.ofd = open(fn, "w")  # Open the file in write mode for output.

    def new_label(self, label):
        # Creates or increments the count for a new label.
        # This is used to manage the generation of unique labels in the code.

        # If the label already exists, increment its occurrence count.
        if label in self.labels:
            self.labels[label] = self.labels[label] + 1
        # If the label is new, initialize its count to 1.
        else:
            self.labels[label] = 1

    def replace_labels(self, s):
        for label in self.labels:
            s = s.replace('<'+label+'>',label+str(self.labels[label]))

        s = s.replace("<FILENAME>", self.base_fn)
        return s
    
    def emit(self, s):
        # Emits (writes) the string `s` to the file after processing it through
        # the label replacement function.
        
        s = self.replace_labels(s)  # Replace any labels before writing.
        self.ofd.write(s)  # Write the processed string to the file.
        self.ofd.write("\n")  # Add a newline after writing.

    def emit_comment(self, comment):
        # Emits a comment to the file. Comments are written with a "//" prefix.
        # If the comment does not end with a newline, it adds one.

        comment = self.replace_labels(comment)  # Replace any labels in the comment.
        self.ofd.write("//")  # Write the comment prefix.
        self.ofd.write(comment)  # Write the comment text.
        
        # If the comment doesn't end with a newline, append a newline.
        if comment[-1] != "\n":
            self.ofd.write("\n")

    def close(self):
        # Closes the file when writing is complete.
        self.ofd.close()  # Close the file descriptor.

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

def pop_pointer_base(code):
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
                    pop_pointer_base(code)
                    code.emit("@THIS")   #Base address of THIS
                    code.emit("M=D")
                case "1":
                    pop_pointer_base(code)
                    code.emit("@THAT")   #Base address of THAT
                    code.emit("M=D")
        case "static":
            pop_pointer_base(code)
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
    code.emit("D=D-M")          #Subtract the two values (D = top - second_top)
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
    code.emit("D=M-D")          #Subtract the two values (D = top - second_top) Why is it M-D here??
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
    code.emit("D=D-M")          #Subtract the two values (D = top - second_top)
    code.emit("@<GREATER>")     #Jump to GREATER if the result of subtraction is 0 (equal)
    code.emit("D;JLT")

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

def main(ifn: str):
    with open(ifn, "r") as input_file:
        # Create an instance of the Code class to output the generated code.
        output_file_name = ifn.split(".")[0] + ".asm"
        code_obj = Code(output_file_name)

        # Process each line in the VM file.
        for line in input_file:
            if line.startswith("//"):  # Skip comment lines
                continue
            words = line.split()  # Split line into words
            if len(words) == 0:   # Skip empty lines
                continue

            # process an actual vm instruction
            op = words[0]             # first word is operation
            args = words[1:]

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
                # TODO : Add more operations
                case _:
                    raise Exception("Unexpected operation " + op)

    code_obj.close()

if __name__ == "__main__":
        print("Command line arguments:", sys.argv)
        main(sys.argv[1])
