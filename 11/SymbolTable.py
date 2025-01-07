class SymbolTable():
    row_count = 0

    def __init__(self):
        self.table = {}

    def reset(self):
        self.table.clear()
        self.row_count = 0

    def define(self, name, type, kind):
        self.table[self.row_count] = [name, type, kind, self.varCount(kind)]
        self.row_count += 1

    def varCount(self, kind):
        count = 0
        for row in self.table:
            if self.table[row][2] == kind:
                count += 1
        return count
    
    def kindOf(self, name):
        kind = None
        for row in self.table:
            if self.table[row][0] == name:
                kind = self.table[row][2]
        return kind
    
    def typeOf(self, name):
        type = None
        for row in self.table:
            if self.table[row][0] == name:
                type = self.table[row][1]
        return type
    
    def indexOf(self, name):
        index = None
        for row in self.table:
            if self.table[row][0] == name:
                index = self.table[row][3]
        return index