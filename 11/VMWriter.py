class VMWriter():

    def __init__(self, output_file):
        self.ofn = output_file
        self.labels = {}
        self.ofd = open(output_file, "w")

    def emit(self, s):
        self.ofd.write(s)
        self.ofd.write("\n")

    def close(self):
        self.ofd.close()

    def writePush(self, segment, index):
        self.emit('push ' + segment + ' ' + str(index))

    def writePop(self, segment, index):
        self.emit('pop ' + segment + ' ' + str(index))

    def writeArithmetic(self, command):
        arithmetic_commands = {
            '+': 'add',
            '-': 'sub',
            '*': 'call Math.multiply 2',
            '/': 'call Math.divide 2',
            '&': 'and',
            '|': 'or',
            '<': 'lt',
            '>': 'gt',
            '=': 'eq',
            'neg': 'neg',
            '~': 'not'
        }
        if command in arithmetic_commands:
            self.emit(arithmetic_commands[command])

    def writeLabel(self, label):
        self.emit('label ' + label)

    def writeGoto(self, label):
        self.emit('goto ' + label)

    def writeIf(self, label):
        self.emit('if-goto ' + label)

    def writeCall(self, name, nArgs):
        self.emit('call ' + name + ' ' + str(nArgs))

    def writeFunction(self, name, nVars):
        self.emit('function ' + name + ' ' + str(nVars))

    def writeReturn(self):
        self.emit('return')