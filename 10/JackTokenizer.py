import os
from pathlib import Path
import re

class JackTokenizer():
    keywords = ['class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return']
    symbols = ['{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~']
    words = []
    current_token = None

    def __init__(self, input_file_name):
        self.ifn = input_file_name
        self.words = self.split_input_file_words(input_file_name)
        self.output_file = os.path.join(os.getcwd(), Path(input_file_name).stem + 'T.xml')
        self.ofd = open(self.output_file, "w")
        self.ofd.write('<tokens>\n')  # XML header for tokens

    def close(self):
        self.ofd.close()

    def split_input_file_words(self, fn):
        self.base_fn = Path(fn).stem
        with open(fn, 'r') as f:
            code = f.read()
        
        # Remove comments
        code = re.sub(r'//.*', '', code) # Single line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL) # Multi-line comments

        # Define token patterns for keywords, symbols, string constants, integer constants, and identifiers
        token_pattern = r"""
        (class|constructor|function|method|field|static|var|int|char|boolean|void|true|false|null|this|let|do|if|else|while|return)  # Keywords
        |([{}()\[\].,;+\-*/&|<>=~])  # Symbols
        |(".*?")  # String constants
        |(\d+)  # Integer constants
        |([a-zA-Z_]\w*)  # Identifiers (must start with letter or underscore)
        """

        # Match all tokens
        tokens = re.findall(token_pattern, code, re.VERBOSE)

        # Flatten the list and filter out empty matches
        self.words = [token for group in tokens for token in group if token]
        return self.words

    def peek(self):
        # Return the next token without consuming it
        if self.hasMoreTokens():
            return self.words[0]  # Peek at the next token
        return None

    def _process(self, input):
        token = self.peek()

        if  token != input:
            raise Exception(f"Expected {input}, got {token}")
        
        token_type = self.tokenType(token)
        
        if token_type == 'KEYWORD':
            self.keyWord(token)
        elif token_type == 'SYMBOL':
            self.symbol(token)
        elif token_type == 'IDENTIFIER':
            self.identifier(token)
        elif token_type == 'INT_CONST':
            self.intVal(token)
        elif token_type == 'STRING_CONST':
            self.stringVal(token)
        
        self.advance()

    def hasMoreTokens(self):
        # Are there more tokens in the input
        return len(self.words) > 0
    
    def advance(self):
        # gets next token from the input and makes it the current token
        if self.hasMoreTokens():
            self.current_token = self.words.pop(0)
            return self.current_token
        print('No more tokens')
        return None

    def tokenType(self, token):
        if token in self.keywords:
            return 'KEYWORD'
        elif token in self.symbols:
            return 'SYMBOL'
        # split into characters and check if number 0-32767,
        # -> INT_CONST, STRING_CONST = Sequence of unicode chars
        # not incl. '"' or '/n'. IDENTIFIER = sequence of letters,
        # digits and '_' not starting with a digit
        elif token.isdigit() and 0 <= int(token) <= 32767:
            return 'INT_CONST'
        elif token.startswith('"') and token.endswith('"'):
            return 'STRING_CONST'
        elif re.match(r'^[a-zA-Z_]\w*$', token):
            return 'IDENTIFIER'
        else:
            return None

    def keyWord(self, keyword):
        self.ofd.write('<keyword> ' + keyword + ' </keyword>\n')
    
    def symbol(self, symbol):
        if symbol == '<':
            symbol = '&lt;'
        elif symbol == '>':
            symbol = '&gt;'
        elif symbol == '&':
            symbol = '&amp;'
        self.ofd.write('<symbol> ' + symbol + ' </symbol>\n')
    
    def identifier(self, string):
        self.ofd.write('<identifier> ' + string + ' </identifier>\n')
    
    def intVal(self, intC):
        self.ofd.write('<integerConstant> ' + str(intC) + ' </integerConstant>\n')
    
    def stringVal(self, stringC):
        stringC = stringC[1:-1]  # Strip quotes
        self.ofd.write('<stringConstant> ' + stringC + ' </stringConstant>\n')