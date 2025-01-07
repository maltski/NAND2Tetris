from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable as ST
from VMWriter import VMWriter as VMW

class CompilationEngine():
    statementKeywords = ['let', 'if', 'while', 'do', 'return']
    op = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
    unaryOp = ['-', '~']
    new_routine = False
    in_subroutinecall = False
    is_array = False
    before_eq = False
    # Status bools
    assigner = False
    caller = False
    expression = False
    if_clause = False
    return_clause = False
    while_clause = False

    class_name = None
    subroutine_name = None
    subroutine_type = None # Constructor / Function / Method
    call_name = None # Name of object calling a method or name of class for functions
    callee_name = None # Name of subroutine being called
    assign_name = None # Name of variable being assigned a new value in the let statement
    var_count = 0 # Amount of local variables in function
    num_expressions = 0
    nested_level = 0 # Helps with label handling in nested loops / clauses.
    total_count = 0 # Same as the above, but only goes up, once every time we are back to "not nested"
    while_count = 0 # The total amount of while clauses in the class
    if_count = 0 # The total amount of if clauses in the class
    field_count = 0 # The total amount of fields in the class
    # Placeholders for symbol table
    name = None
    type = None
    kind = None

    def __init__(self, input_file_name, output_file_name):
        self.jackT = JackTokenizer(input_file_name)
        self.vmw = VMW(output_file_name)
        self.class_table = ST()
        self.subroutine_table = ST()

    def close(self):
        self.vmw.close()

    def __exit__(self, *args):
        self.close()

    def _process(self, word):
        self.jackT._process(word)

    def new_entry(self, name, type, kind):
        if kind in ['static', 'this']:
            self.class_table.define(name, type, kind)
        else:
            self.subroutine_table.define(name, type, kind)

    def compileClass(self):
        # Compiles a complete class
        self._process('class')  # "class" keyword
        self.class_name = self.jackT.peek()
        self._process(self.class_name)
        self._process('{')  # Opening brace
        while self.jackT.peek() in ['static', 'field']:
            self.compileClassVarDec()

        while self.jackT.peek() in ['constructor', 'function', 'method']:
            self.compileSubroutine()
        self._process('}')  # Closing brace
        self.class_table.reset()

    def compileClassVarDec(self):
        # Compiles a static variable or field declaration
        if self.jackT.peek() == 'static':
            self._process('static')
            self.kind = 'static'
        elif self.jackT.peek() == 'field':
            self._process('field')
            self.kind = 'this'
        self.compileVarDec()

    def compileSubroutine(self):
        # Compiles a complete method, function, or constructor
        self.new_routine = True
        if self.jackT.peek() == 'constructor':
            self._process('constructor')
            self.subroutine_type = 'constructor'
        elif self.jackT.peek() == 'function':
            self._process('function')
            self.subroutine_type = 'function'
        elif self.jackT.peek() == 'method':
            self._process('method')
            self.subroutine_type = 'method'
        # type
        return_type = self.jackT.peek()
        if return_type == 'void':
            self._process('void')
        elif return_type == 'int':
            self._process('int')
        elif return_type == 'char':
            self._process('char')
        elif return_type == 'boolean':
            self._process('boolean')
        else:
            self.compileTerm() # class type
        # subroutine name
        self.subroutine_name = self.jackT.peek()
        self.compileTerm()
        self.compileSubroutineBody()
        self.subroutine_table.reset()

    def compileParameterList(self):
        # Compiles a (possibly empty) parameter list. Does not handle the enclosing parentheses tokens
        while self.jackT.peek() != ')':
            self.kind = 'argument'
            self.type = self.jackT.peek()
            self.compileTerm() # type
            self.name = self.jackT.peek()
            self.new_entry(self.name, self.type, self.kind)
            self.compileTerm() # var Name
            if self.jackT.peek() == ',':
                self._process(',')

    def compileSubroutineBody(self):
        # Compiles a subroutine's body
        self._process('{')
        while self.jackT.peek() == 'var':
            self.kind = 'local'
            self._process('var')
            self.compileVarDec()
        # Special handling for constructor: Allocate memory and assign it to 'this'
        if self.subroutine_type == 'constructor':
            self.var_count = 0
            self.vmw.writeFunction(self.class_name + '.' + self.subroutine_name, str(self.var_count))            
            # Allocate memory for the object
            self.vmw.writePush('constant', self.field_count)
            self.field_count = 0
            self.vmw.writeCall('Memory.alloc', 1)  # Allocate memory for 'n' fields
            self.vmw.writePop('pointer', 0)  # Store the allocated memory in 'this' (pointer 0)
        elif self.subroutine_type == 'method':
            self.vmw.writeFunction(self.class_name + '.' + self.subroutine_name, str(self.var_count))
            self.vmw.writePush('argument', 0)
            self.vmw.writePop('pointer', 0)
        else:
            self.vmw.writeFunction(self.class_name + '.' + self.subroutine_name, str(self.var_count))
        self.var_count = 0
        self.compileStatements()
        self._process('}')

    def compileVarDec(self):
        # Compiles a variable declaration
        field = False
        if self.jackT.current_token == 'field':
            field = True
        if self.jackT.peek() == 'int':
            self.type = 'int'
            self._process('int')
        elif self.jackT.peek() == 'char':
            self.type = 'char'
            self._process('char')
        elif self.jackT.peek() == 'boolean':
            self.type = 'boolean'
            self._process('boolean')
        else:
            self.type = self.jackT.peek()
            self.compileTerm() # class type
        # varName
        self.name = self.jackT.peek()
        self.new_entry(self.name, self.type, self.kind)
        self.compileTerm() # first var name
        self.var_count += 1
        if field:
            self.field_count +=1
        while self.jackT.peek() == ',': # If additional
            self._process(',')
            self.var_count += 1
            if field:
                self.field_count +=1
            self.name = self.jackT.peek()
            self.new_entry(self.name, self.type, self.kind)
            self.compileTerm()
        self._process(';')

    def compileStatements(self):
        while self.jackT.peek() in self.statementKeywords:
            if self.jackT.peek() == 'let':
                self.compileLet()
            elif self.jackT.peek() == 'if':
                self.compileIf()
            elif self.jackT.peek() == 'while':
                self.compileWhile()
            elif self.jackT.peek() == 'do':
                self.compileDo()
            elif self.jackT.peek() == 'return':
                self.compileReturn()

    def compileLet(self):
        # compiles a let statement
        with_index = False
        self._process('let')
        self.assign_name = self.jackT.peek()
        self.compileTerm() # var name
        if self.before_eq: # If the array element is in the form a[i] and not a
            with_index = True
        self._process('=')
        self.before_eq = False
        self.assigner = True
        self.compileExpression() # Compile the value to be assigned
        self.assigner = False
        if with_index:
            if self.subroutine_table.typeOf(self.assign_name) == 'Array' or self.class_table.typeOf(self.assign_name) == 'Array':     
                if self.is_array:
                    self.vmw.writePop('temp', 0) # Temporarily store the value to be assigned
                    self.vmw.writePop('pointer', 1) # Set `that` pointer to the target array element
                    self.vmw.writePush('temp', 0) # Push the value back onto the stack
                    self.vmw.writePop('that', 0) # Assign the value to the array element
        else:
            if self.subroutine_table.kindOf(self.assign_name) is not None:
                kind = self.subroutine_table.kindOf(self.assign_name)
                index = self.subroutine_table.indexOf(self.assign_name)
                self.vmw.writePop(kind, index)
            elif self.class_table.kindOf(self.assign_name) is not None:
                kind = self.class_table.kindOf(self.assign_name)
                index = self.class_table.indexOf(self.assign_name)
                self.vmw.writePop(kind, index)
        self._process(';')
        self.is_array = False
        self.assign_name = None

    def compileIf(self):
        self.if_count += 1
        start_label = 'IF' + str(self.total_count) + str(self.if_count)
        false_label = 'IF_FALSE' + str(self.total_count) + str(self.if_count)
        end_label = 'IF_END' + str(self.total_count) + str(self.if_count)
        self.nested_level += 1
        self._process('if')
        self.if_clause = True
        self.compileExpression()
        self.if_clause = False
        self.vmw.writeIf(start_label)
        self.vmw.writeGoto(false_label)
        self.vmw.writeLabel(start_label)
        self._process('{')
        self.compileStatements()
        self._process('}')
        if self.jackT.peek() == 'else':
            self.vmw.writeGoto(end_label)
            self.vmw.writeLabel(false_label)
            self._process('else')
            self._process('{')
            self.compileStatements()
            self._process('}')
            self.vmw.writeLabel(end_label)
        else:
            self.vmw.writeLabel(false_label)
        self.nested_level -= 1
        if self.nested_level == 0:
            self.total_count += 1

    def compileWhile(self):
        self.while_count += 1
        start_label = 'WHILE' + str(self.total_count) + str(self.while_count)
        end_label = 'WHILE_END' + str(self.total_count) + str(self.while_count)
        self.nested_level += 1
        self._process('while')
        self.vmw.writeLabel(start_label)
        self.while_clause = True
        self.compileExpression()
        self.while_clause = False
        self.vmw.writeArithmetic('~')
        self.vmw.writeIf(end_label)
        self._process('{')
        self.compileStatements()
        self.vmw.writeGoto(start_label)
        self.vmw.writeLabel(end_label)
        self._process('}')
        self.nested_level -= 1
        if self.nested_level == 0:
            self.total_count += 1

    def compileDo(self):
        self._process('do')
        self.call_name = self.jackT.peek()
        self.caller = True
        self.compileTerm() # subroutine name or class / var name
        self._process(';')
        self.is_array = False

    def compileReturn(self):
        self._process('return')
        if self.jackT.peek() != ';':
            self.return_clause = True
            self.compileExpression()
            self.return_clause = False
        else:
            self.vmw.writePush('constant', 0)
        self.vmw.writeReturn()
        self._process(';')

    def make_call(self):
        instance_name = None
        method_class_name = None
        if self.subroutine_table.kindOf(self.call_name.split('.')[0]) is not None or self.class_table.kindOf(self.call_name.split('.')[0]) is not None:
            # If the first part of call_name refers to a variable in subroutine or class scope, it's an object
            instance_name = self.call_name.split('.')[0]
            # Get the class type of the instance
            method_class_name = self.subroutine_table.typeOf(instance_name) or self.class_table.typeOf(instance_name)
            self.vmw.writeCall(method_class_name + '.' + self.call_name.split('.')[1], self.num_expressions + 1)  # Extra argument for 'this' or object reference
        elif '.' not in self.call_name:
            # If there's no '.', assume it's a method in the current class (calling on 'this')
            instance_name = 'this'  # Implicit call on current instance
            method_class_name = self.class_name
            self.vmw.writeCall(method_class_name + '.' + self.callee_name, self.num_expressions + 1)     
        else:
            # Function or constructor call (no 'this' or object reference needed)
            self.vmw.writeCall(self.call_name, self.num_expressions)
        self.caller = False
        self.expression = False
        if self.assign_name is None:
            self.vmw.writePop('temp', 0)
        
    def compileExpression(self):
        # term (op term)*
        if self.jackT.peek() != ')':
            if self.jackT.peek() != ';':
                self.compileTerm()
                while self.jackT.peek() in self.op:
                    operator = self.jackT.peek()
                    self._process(self.jackT.peek())
                    self.compileTerm()
                    self.vmw.writeArithmetic(operator)

    def compileTerm(self):
        # Compiles a term.
        token = self.jackT.peek()
        if self.jackT.tokenType(token) == 'INT_CONST':
            self.vmw.writePush('constant', token)
            self._process(token)
    
        # String constant
        elif self.jackT.tokenType(token) == 'STRING_CONST':
            string_value = self.jackT.peek()
            string_value = string_value[1:-1] # Strip quotes
            length = len(string_value)
            self.vmw.writePush('constant', length) # Push the length of the string
            self.vmw.writeCall('String.new', 1) # Create a new String object in memory
            for char in string_value:
                self.vmw.writePush('constant', ord(char)) # Push each character's ASCII value
                self.vmw.writeCall('String.appendChar', 2)
            self._process(self.jackT.peek())
        
        # Keyword constant (true, false, null, this)
        elif self.jackT.tokenType(token) == 'KEYWORD':
            if token == 'true':
                self.vmw.writePush('constant', 0)
                self.vmw.writeArithmetic('~')
            elif token == 'false' or token == 'null':
                self.vmw.writePush('constant', 0)
            elif token == 'this':
                self.vmw.writePush('pointer', 0)
            self._process(token)
        
        # Variable name, array access, or subroutine call
        elif self.jackT.tokenType(token) == 'IDENTIFIER':
            identifier = self.jackT.peek()
            self._process(identifier)

            if self.jackT.peek() != '[':
                if self.expression or self.caller or self.if_clause or self.while_clause or self.return_clause or self.assigner or self.is_array:
                    if self.subroutine_table.kindOf(identifier) is not None:
                        kind = self.subroutine_table.kindOf(identifier)
                        index = self.subroutine_table.indexOf(identifier)
                        if kind == 'argument' and self.subroutine_type == 'method':
                            self.vmw.writePush(kind, index + 1)
                        else:
                            self.vmw.writePush(kind, index)
                    elif self.class_table.kindOf(identifier) is not None:
                        kind = self.class_table.kindOf(identifier)
                        index = self.class_table.indexOf(identifier)
                        self.vmw.writePush(kind, index)

            if self.jackT.peek() == '[': # Array access: varName[expression]
                element_access = False
                if self.is_array or self.in_subroutinecall: # If we already are in an array expression and encounter another '[', we know it is an element in the index. If we find it in a subroutinecall expression, it is also accessed
                    element_access = True
                self.is_array = True
                if self.subroutine_table.kindOf(identifier) is not None:
                    array_kind = self.subroutine_table.kindOf(identifier)
                    array_index = self.subroutine_table.indexOf(identifier)
                elif self.class_table.kindOf(identifier) is not None:
                    array_kind = self.class_table.kindOf(identifier)
                    array_index = self.class_table.indexOf(identifier)

                self._process('[')
                self.compileExpression()  # Array index expression
                self.vmw.writePush(array_kind, array_index)
                self.vmw.writeArithmetic('+')  # Compute array access address

                if self.assigner or element_access: # If the array element is part of an expression in a let statement, in a subroutine call expression or in an array index expression
                    self.vmw.writePop('pointer', 1)  # Use that as 'that' pointer
                    self.vmw.writePush('that', 0)  # Access the array element
                else:
                    self.before_eq = True # If it is a let statement, the array element is before the '='
                self._process(']')

            elif self.jackT.peek() == '(':
                self.callee_name = self.jackT.current_token
                self._process('(')
                if self.new_routine: # Subroutine declaration: subroutineName(parameterList)
                    self.compileParameterList()
                    self.new_routine = False
                else: # Subroutine call: subroutineName(expressionList)
                    self.in_subroutinecall = True
                    self.expression = True
                    if not '.' in self.call_name:
                        self.subroutine_type = 'method'
                        self.vmw.writePush('pointer', 0) # Push 'this' (current object)
                    self.num_expressions = self.compileExpressionList()
                    self.make_call()
                    self.in_subroutinecall = False
                while self.jackT.peek() == ')':
                    self._process(')')

            elif self.jackT.peek() == '.': # Subroutine call: className.subroutineName(expressionList)
                self.call_name = self.jackT.current_token
                self._process('.')
                self.callee_name = self.jackT.peek()
                self.call_name = self.call_name + '.' + self.callee_name
                self.compileTerm() # subroutineName

        # Parenthesized expression: (expression)
        elif self.jackT.peek() == '(':
            self._process('(')
            self.compileExpression() # Recursively compile the expression inside the parenthesis
            if self.jackT.peek() == ')':
                self._process(')')
        
        # Unary operator followed by a term: unaryOp term
        elif self.jackT.peek() in self.unaryOp:
            unary_op = self.jackT.peek()
            self._process(unary_op) # Process the unary operator
            self.compileTerm() # Recursively compile the term
            if unary_op == '-':
                self.vmw.writeArithmetic('neg') # Negate the term
            elif unary_op == '~':
                self.vmw.writeArithmetic('~') # Bitwise NOT

    def compileExpressionList(self):
        # Compiles a (possibly empty) comma-separated list of expressions.
        # Returns the number of expressions in the list
        # (expression (',' expression)*)?
        count = 0
        if self.jackT.peek() != ')': # Expression list can be empty, only process if not ')'
            self.compileExpression() # Compile first expression
            count += 1
            while self.jackT.peek() == ',': # If there's a comma, more expressions follow
                self._process(',')
                self.compileExpression()
                count += 1
        return count