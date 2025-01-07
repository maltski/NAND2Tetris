from JackTokenizer import JackTokenizer

class CompilationEngine():
    statementKeywords = ['let', 'if', 'while', 'do', 'return']
    op = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
    unaryOp = ['-', '~']
    indentation = 0
    new_routine = False

    def __init__(self, input_file_name, output_file_name):
        self.jackT = JackTokenizer(input_file_name)
        self.ofn = output_file_name
        self.ofd = open(output_file_name, "w")

    def close(self):
        self.jackT.ofd.write('</tokens>\n')  # XML footer for tokens
        self.ofd.close()
        self.jackT.close()  # Also close the tokenizer's output file

    def __exit__(self, *args):
        self.close()

    def indent(self):
        # indents by one tab (2 spaces)
        self.indentation += 1

    def unindent(self):
        # Unindents by one tab (2 spaces)
        self.indentation -= 1

    def writeIndented(self, text):
        # Writes with the current indentation level
        self.ofd.write('  ' * self.indentation + text)

    def _process(self, word):
        self.jackT._process(word)

        token_type = self.jackT.tokenType(word)
        
        if token_type == 'KEYWORD':
            self.keyWord(word)
        elif token_type == 'SYMBOL':
            self.symbol(word)
        elif token_type == 'IDENTIFIER':
            self.identifier(word)
        elif token_type == 'INT_CONST':
            self.intVal(word)
        elif token_type == 'STRING_CONST':
            self.stringVal(word)

    def keyWord(self, keyword):
        self.writeIndented('<keyword> ' + keyword + ' </keyword>\n')
    
    def symbol(self, symbol):
        if symbol == '<':
            symbol = '&lt;'
        elif symbol == '>':
            symbol = '&gt;'
        elif symbol == '&':
            symbol = '&amp;'
        self.writeIndented('<symbol> ' + symbol + ' </symbol>\n')
    
    def identifier(self, string):
        self.writeIndented('<identifier> ' + string + ' </identifier>\n')
    
    def intVal(self, intC):
        self.writeIndented('<integerConstant> ' + str(intC) + ' </integerConstant>\n')
    
    def stringVal(self, stringC):
        stringC = stringC[1:-1]  # Strip quotes
        self.writeIndented('<stringConstant> ' + stringC + ' </stringConstant>\n')

    def compileClass(self):
        # Compiles a complete class
        self.writeIndented('<class>\n')
        self.indent()
        self._process('class')  # "class" keyword
        self.compileTerm()  # Class name
        self._process('{')  # Opening brace

        while self.jackT.peek() in ['static', 'field']:
            self.compileClassVarDec()

        while self.jackT.peek() in ['constructor', 'function', 'method']:
            self.compileSubroutine()

        self._process('}')  # Closing brace
        self.unindent()
        self.writeIndented('</class>\n')

    def compileClassVarDec(self):
        # Compiles a static variable or field declaration
        self.writeIndented('<classVarDec>\n')
        self.indent()
        if self.jackT.peek() == 'static':
            self._process('static')
        elif self.jackT.peek() == 'field':
            self._process('field')
        self.compileVarDec()
        self.unindent()
        self.writeIndented('</classVarDec>\n')

    def compileSubroutine(self):
        # Compiles a complete method, function, or constructor
        self.writeIndented('<subroutineDec>\n')
        self.indent()
        self.new_routine = True
        if self.jackT.peek() == 'constructor':
            self._process('constructor')
        elif self.jackT.peek() == 'function':
            self._process('function')
        elif self.jackT.peek() == 'method':
            self._process('method')
        
        # type
        if self.jackT.peek() == 'void':
            self._process('void')
        elif self.jackT.peek() == 'int':
            self._process('int')
        elif self.jackT.peek() == 'char':
            self._process('char')
        elif self.jackT.peek() == 'boolean':
            self._process('boolean')
        else:
            self.compileTerm() # class type

        # subroutine name
        self.compileTerm()
        
        self.compileSubroutineBody()
        self.unindent()
        self.writeIndented('</subroutineDec>\n')

    def compileParameterList(self):
        # Compiles a (possibly empty) parameter list. Does not handle the enclosing parentheses tokens
        self.writeIndented('<parameterList>\n')
        self.indent()
        while self.jackT.peek() != ')':
            self.compileTerm() # type
            self.compileTerm() # var Name
            if self.jackT.peek() == ',':
                self._process(',')
        self.unindent()
        self.writeIndented('</parameterList>\n')

    def compileSubroutineBody(self):
        # Compiles a subroutine's body
        self.writeIndented('<subroutineBody>\n')
        self.indent()
        self._process('{')
        while self.jackT.peek() == 'var':
            self.writeIndented('<varDec>\n')
            self.indent()
            self._process('var')
            self.compileVarDec()
            self.unindent()
            self.writeIndented('</varDec>\n')
        self.compileStatements()
        self._process('}')
        self.unindent()
        self.writeIndented('</subroutineBody>\n') 

    def compileVarDec(self):
        # Compiles a variable declaration
        if self.jackT.peek() == 'int':
            self._process('int')
        elif self.jackT.peek() == 'char':
            self._process('char')
        elif self.jackT.peek() == 'boolean':
            self._process('boolean')
        else:
            self.compileTerm() # class type

        # varName
        self.compileTerm() # first var name
        while self.jackT.peek() == ',': # If additional
            self._process(',')
            self.compileTerm()
        self._process(';')

    def compileStatements(self):
        self.writeIndented('<statements>\n')
        self.indent()
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
        self.unindent()
        self.writeIndented('</statements>\n')

    def compileLet(self):
        # compiles a let statement
        self.writeIndented('<letStatement>\n')
        self.indent()
        self._process('let')
        self.compileTerm() # var name
        if self.jackT.peek() == '[':
            self._process('[')
            self.compileExpression()
            self._process(']')
        self._process('=')
        self.compileExpression()
        self._process(';')
        self.unindent()
        self.writeIndented('</letStatement>\n')

    def if_while_base(self):
        self._process('(')
        self.compileExpression()
        self._process(')')
        self._process('{')
        self.compileStatements()
        self._process('}')

    def compileIf(self):
        self.writeIndented('<ifStatement>\n')
        self.indent()
        self.jackT.peek() == 'if'
        self._process('if')
        self.if_while_base()
        if self.jackT.peek() == 'else':
            self._process('else')
            self._process('{')
            self.compileStatements()
            self._process('}')
        self.unindent()
        self.writeIndented('</ifStatement>\n')

    def compileWhile(self):
        self.writeIndented('<whileStatement>\n')
        self.indent()
        self._process('while')
        self.if_while_base()
        self.unindent()
        self.writeIndented('</whileStatement>\n')

    def compileDo(self):
        self.writeIndented('<doStatement>\n')
        self.indent()
        self._process('do')
        self.compileTerm() # subroutine name or class / var name
        if self.jackT.peek() == '.':
            self._process('.')
            self.compileTerm() # subroutine name
        self._process(';')
        self.unindent()
        self.writeIndented('</doStatement>\n')

    def compileReturn(self):
        self.writeIndented('<returnStatement>\n')
        self.indent()
        self._process('return')
        if self.jackT.peek() != ';':
            self.compileExpression()
        self._process(';')
        self.unindent()
        self.writeIndented('</returnStatement>\n')
        
    def compileExpression(self):
        # term (op term)*
        self.writeIndented('<expression>\n')
        self.indent()
        if self.jackT.peek() != ')':
            if self.jackT.peek() != ';':
                self.termTag()
        while self.jackT.peek() in self.op:
            self._process(self.jackT.peek())
            self.termTag()
        self.unindent()
        self.writeIndented('</expression>\n')

    def termTag(self):
        self.writeIndented('<term>\n')
        self.indent()
        self.compileTerm()
        self.unindent()
        self.writeIndented('</term>\n')

    def compileTerm(self):
        # Compiles a term.
        # If the current token is an identifier,
        # the routine must resolve it into a variable,
        # an array entry, or a subroutine call.
        # A single lookahead token, which may be [, (, or .,
        # suffices to distinguish between possibilities.
        # Any other token is not part of this term
        # and should not be advanced over
        # integerConstant | stringConstant | keywordConstant | varName |
        # varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
        if self.jackT.tokenType(self.jackT.peek()) == 'INT_CONST':
            self._process(self.jackT.peek())
    
        # String constant
        elif self.jackT.tokenType(self.jackT.peek()) == 'STRING_CONST':
            self._process(self.jackT.peek())
        
        # Keyword constant (true, false, null, this)
        elif self.jackT.tokenType(self.jackT.peek()) == 'KEYWORD':
            self._process(self.jackT.peek())
        
        # Variable name, array access, or subroutine call
        elif self.jackT.tokenType(self.jackT.peek()) == 'IDENTIFIER':
            self._process(self.jackT.peek())
            if self.jackT.peek() == '[':  # Array access: varName[expression]
                self._process('[')
                self.compileExpression()
                self._process(']')
            elif self.jackT.peek() == '(':
                self._process('(')
                if self.new_routine:                # Subroutine declaration: subroutineName(parameterList)
                    self.compileParameterList()
                    self.new_routine = False
                else:                               # Subroutine call: subroutineName(expressionList)
                    self.compileExpressionList()
                self._process(')')
            elif self.jackT.peek() == '.':  # Subroutine call: className.subroutineName(expressionList)
                self._process('.')
                self.compileTerm()  # subroutineName
        
        # Parenthesized expression: (expression)
        elif self.jackT.peek() == '(':
            self._process('(')
            if self.jackT.peek() == '~':
                self._process(self.jackT.peek())
                self.termTag()
            else:               
                self.compileExpression()
            self._process(')')
        
        # Unary operator followed by a term: unaryOp term
        elif self.jackT.peek() in self.unaryOp:
            self._process(self.jackT.peek())
            self.termTag()

    def compileExpressionList(self):
        # Compiles a (possibly empty) comma-separated list of expressions.
        # Returns the number of expressions in the list
        # (expression (',' expression)*)?
        self.writeIndented('<expressionList>\n')
        self.indent()
        count = 0
        if self.jackT.peek() != ')':  # Expression list can be empty, only process if not ')'
            self.compileExpression()  # Compile first expression
            count += 1
            while self.jackT.peek() == ',':  # If there's a comma, more expressions follow
                self._process(',')
                self.compileExpression()
                count += 1
        self.unindent()
        self.writeIndented('</expressionList>\n')
        return count