from ply.lex import lex
import re
import control_flags

class TeslangLexer(object):
    def find_token_column(self, token):
        last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
        if last_cr < 0:
            last_cr = 0
        return token.lexpos - last_cr

    def build(self):
        self.lexer = lex(object=self)

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    tokens = (
        'FN',
        'STRING',
        'DO',
        'ID',
        'LPAREN',
        'RPAREN',
        'AS',
        'VECTOR',
        'COMMENT',
        'LESS_THAN',
        'INT',
        'GREATER_THAN',
        'LCURLYEBR',
        'RCURLYEBR',
        'DBL_COLON',
        'EQ',
        'NUMBER',
        'SEMI_COLON',
        'FOR',
        'TO',
        'LEN',
        'BEGIN',
        'PLUS',
        'LSQUAREBR',
        'RSQUAREBR',
        'END',
        'RETURN',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'COLON',
        'COMMA',
        'MOD',
        'NULL',
        'AND',
        'OR',
        'NOT',
        'EQUAL',
        'NOT_EQUAL',
        'LESS_THAN_EQUAL_TO',
        'GREATER_THAN_EQUAL_TO',
        'WHILE',
        'IF',
        'ELSE',
        'STR',
        'BOOLEAN',
        'QUESTION',

        'SCAN',
        'PRINT',
        'LIST',
        'EXIT',
        'TYPE'
    )

    t_NULL= r'null'
    t_VECTOR = r'vector'
    t_INT = r'int'
    t_STR = r'str'
    t_BOOLEAN = r'bool'

    t_FN = r'fn'
    t_AS = r'as'
    t_FOR = r'for'
    t_WHILE =r'while'
    t_DO = r'do'
    t_IF = r'if'
    t_ELSE = r'else'
    t_TO = r'to'
    t_LEN = r'length'
    t_BEGIN = r'begin'
    t_END = r'end'
    t_RETURN = r'return'
    t_SCAN = r'scan'
    t_PRINT = r'print'
    t_LIST = r'list'
    t_EXIT = r'exit'

    t_OR      = r'\|\|'
    t_AND     = r'&&'
    t_NOT     = r'!'
    t_QUESTION = r'\?'
    t_EQ = r'='
    t_EQUAL   = r'=='
    t_NOT_EQUAL=r'!='
    t_LESS_THAN_EQUAL_TO=r'<='
    t_GREATER_THAN_EQUAL_TO=r'>='
    t_LESS_THAN = r'<'
    t_GREATER_THAN = r'>'

    t_MOD     = r'%'
    t_PLUS    = r'\+'
    t_MINUS   = r'-'
    t_TIMES   = r'\*'
    t_DIVIDE  = r'/'

    t_COLON   = r':'
    t_COMMA   = r','
    t_LPAREN  = r'\('
    t_RPAREN  = r'\)'
    t_LSQUAREBR = r'\['
    t_RSQUAREBR = r'\]'
    t_SEMI_COLON = r';'
    t_LCURLYEBR = r'{'
    t_RCURLYEBR = r'}'
    t_DBL_COLON = r'::'
    # t_STRING = r'(\' [^\']* [\'] | ["]  [^"]* ["])'

    def t_TYPE(self, t):
        r'\b(int|str|vector|null|bool)\b'
        return t

    def t_NUMBER(self,t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_STRING(self, t):
        # String literal - (x|y) where x shouldn't match \ , \n , ", '
        r'[\"\']([^\'\"\n\\]|(\\.))*?[\"\']'
        if t.value[0] != t.value[-1]:
            print(f'Illegal character {t.value[0]!r} at line {t.lineno}')
            t.lexer.skip(1)
        t.value = re.sub(r'\\', r'', t.value[1:-1])
        return t

    def t_ID(self,t):
        r'[a-zA-Zـ][a-zA-Z0-9]*'

        keywords = {
            'fn' : 'FN',
            'as' : 'AS',
            'vector' : 'VECTOR',
            'int' : 'INT',
            'str' : 'STR',
            'bool' : 'BOOLEAN',
            'for' : 'FOR',
            'while' : 'WHILE',
            'do' : 'DO',
            'if' : 'IF',
            'else' : 'ELSE',
            'to' : 'TO',
            'length' : 'LEN',
            'begin' : 'BEGIN',
            'end' : 'END',
            'return' : 'RETURN',
            'null' : 'NULL',
            'scan' : 'SCAN',
            'print' : 'PRINT',
            'list' : 'LIST',
            'exit' : 'EXIT',
        }

        t.type = keywords.get(t.value, 'ID')
        return t

    def t_COMMENT(self,t):
        r'<%(.|\n)*?%>'
        t.lexer.lineno += t.value.count('\n')
        return

    # Ignored token with an action associated with it
    def t_ignore_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count('\n')
    t_ignore  = ' \t'
    # Error handler for illegal characters
    def t_error(self, t):
        control_flags.lexer_failed = True
        print(f'Illegal character {t.value[0]!r} at line {t.lineno}')
        t.lexer.skip(1)

    # lexer = lex.build()
    # data = '''
    # <% Comment %>
    # <% Comment int >< >% %>
    # <%
    # comment 
    # int
    # scan()
    # print()
    # %>
    # fn sum(numlist as vector) <int> {
    #     result :: int = 0;

    #     <% Comment %>
    #     test :: str = "test";
    #     test2 :: str = 'test'
    #     for (i = 0 to length(numlist))
    #     begin
    #         result = result + numlist[i];
    #         <% Comment <% %>
    #         <% Comment int >< >% %>
    #         <%
    #         comment 
    #         <% htfhfg %>
    #         int
    #         scan()
    #         print()
    #         %>
    #         scan();
    #         exit();
    #     end
    #     return result;
    # }
    # '''

    # # Give the lexer some input
    # lexer.input(data)


    # print(" Line | Column | Token | Value ")
    # print("-------------------------------")
    # while True:
    #     tok = lexer.token()
    #     if not tok: 
    #         break
    #     print(tok.lineno-1,"    ",find_token_column(data,tok),"    ",tok.type,"    ",tok.value)
