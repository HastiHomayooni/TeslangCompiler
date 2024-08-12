import ply.yacc as yacc
from TeslangLexer import *
from AST import *
from colors import bcolors
import control_flags

class FilePosition(object):
    def __init__(self, line):
        self.line = line


def getPosition(p):
    return FilePosition(p.lexer.lexer.lineno - 1)


class TeslangParser(object):
    def __init__(self, pre_parse=False):
        self.pre_parse = pre_parse
        self.scanner = TeslangLexer()
        self.scanner.build()

    tokens = TeslangLexer.tokens

    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),             
        ('left', 'OR', 'AND'),    
        ('left', 'EQUAL', 'NOT_EQUAL', 'GREATER_THAN', 'LESS_THAN', 'GREATER_THAN_EQUAL_TO', 'LESS_THAN_EQUAL_TO'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MOD'),
        ('left', 'QUESTION', 'COLON'),
        ('left', 'COMMA'),
        ('right', 'EQ', 'NOT'), 
    )

    # Rule 1
    def p_prog(self, p: yacc.YaccProduction):
        '''prog : empty
                | func prog'''
        if len(p) == 3:
            p[0] = Program(func=p[1], prog=p[2], pos=getPosition(p))

    # Rule 2
    def p_func(self, p: yacc.YaccProduction):
        """func : FN ID LPAREN flist RPAREN LESS_THAN TYPE GREATER_THAN LCURLYEBR body RCURLYEBR
                | FN ID LPAREN flist RPAREN LESS_THAN TYPE GREATER_THAN EQ GREATER_THAN RETURN expr SEMI_COLON"""
        if isinstance(p[10], Body) or p[10] is None:
            p[0] = FunctionDef(rettype=p[7], name=p[2], fmlparams=p[4], body=p[10], pos=getPosition(p))
        else:
            p[0] = BodyLessFunctionDef(rettype=p[7], name=p[2], fmlparams=p[4], expr=p[10], pos=getPosition(p))

    def p_func_parameter_error(self, p: yacc.YaccProduction):
        '''func : FN ID LPAREN error RPAREN LESS_THAN TYPE GREATER_THAN LCURLYEBR body RCURLYEBR'''
        p[0] = FunctionDef(rettype=p[7], name=p[2], fmlparams=None, body=p[10], pos=getPosition(p))
        self.handle_error('function definition', p[4])

    def p_func_missing_return_type_error(self, p: yacc.YaccProduction):
        '''func : FN ID LPAREN flist RPAREN LESS_THAN error GREATER_THAN LCURLYEBR body RCURLYEBR'''
        p[0] = FunctionDef(rettype='int', name=p[2], fmlparams=p[4], body=p[10], pos=getPosition(p))
        self.handle_error('function return type', p[7])

    def p_body(self, p: yacc.YaccProduction):
        '''body : empty 
                | stmt body'''
        if len(p) == 3:
            p[0] = Body(statement=p[1], body=p[2])

    def p_stmt(self, p: yacc.YaccProduction):
        '''stmt : expr SEMI_COLON
                | defvar SEMI_COLON
                | func SEMI_COLON
                | single_if
                | if_with_else
                | while_loop
                | DO stmt WHILE LSQUAREBR LSQUAREBR expr RSQUAREBR RSQUAREBR 
                | for_loop
                | block
                | return_instr SEMI_COLON'''
        
        p[0] = p[1]

    def p_stmt_error(self, p):
        '''stmt : error SEMI_COLON
                | error'''
        self.handle_error('statement', p[1])

    def p_single_if(self, p: yacc.YaccProduction):
        '''single_if : IF LSQUAREBR LSQUAREBR expr RSQUAREBR RSQUAREBR stmt'''
        p[0] = IfOrIfElseInstruction(cond=p[4], if_statement=p[7], \
                                     else_statement=None, pos=getPosition(p))
    
    def p_if_with_else(self, p: yacc.YaccProduction):
        '''if_with_else : IF LSQUAREBR LSQUAREBR expr RSQUAREBR RSQUAREBR stmt ELSE stmt'''
        p[0] = IfOrIfElseInstruction(cond=p[4], if_statement=p[7], \
                                     else_statement=p[9], pos=getPosition(p))

    def p_while_loop(self, p: yacc.YaccProduction):
        '''while_loop : WHILE LSQUAREBR LSQUAREBR expr RSQUAREBR RSQUAREBR stmt'''
        p[0] = WhileInstruction(cond=p[4], while_statement=p[7], pos=getPosition(p))

    def p_for_loop(self, p: yacc.YaccProduction):
        '''for_loop : FOR LPAREN ID EQ expr TO expr RPAREN stmt'''
        p[0] = ForInstruction(id=p[3], start_expr=p[5], end_expr=p[7], \
                              for_statement=p[9], pos=getPosition(p))

    def p_block(self, p: yacc.YaccProduction):
        '''block : BEGIN body END'''
        p[0] = Block(body=p[2])

    def p_return_instr(self, p: yacc.YaccProduction):
        '''return_instr : RETURN expr'''
        p[0] = ReturnInstruction(expr=p[2], pos=getPosition(p))

    def p_defvar(self, p: yacc.YaccProduction):
        '''defvar : ID DBL_COLON TYPE 
               | ID DBL_COLON TYPE EQ expr'''
        if len(p) == 4:
            p[0] = VariableDecl(type=p[3], id=p[1], expr=None, pos=getPosition(p))
        elif len(p) == 6:
            p[0] = VariableDecl(type=p[3], id=p[1], expr=p[5], pos=getPosition(p))

    def p_flist(self, p: yacc.YaccProduction):
        '''flist : empty
              | ID AS TYPE 
              | ID AS TYPE COMMA flist'''
        if len(p) == 4:
            p[0] = ParametersList(parameters=[Parameter(type=p[3], id=p[1])])
        elif len(p) == 6:
            p[0] = ParametersList(parameters=p[5].parameters + [Parameter(type=p[3], id=p[1])])

    def p_flist_error(self, p):
        '''flist : error AS TYPE COMMA flist
                 | ID error TYPE COMMA flist
                 | ID AS error COMMA flist
                 | ID AS TYPE COMMA error'''
        p[0] = ParametersList(parameters=[])
        for i in range(1, len(p)):
            if p[i].__class__.__name__ == 'LexToken':
                self.handle_error('function parameters list', p[i])
                break

    def p_clist(self, p: yacc.YaccProduction):
        '''clist : empty
                 | expr
                 | expr COMMA clist'''
        if len(p) == 2:
            exprs = [] if p[1] == [] else [p[1]]
            p[0] = ExprList(exprs=exprs)
        elif len(p) == 4:
            p[0] = ExprList(exprs=p[3].exprs + [p[1]])

    def p_in_methods(self,p: yacc.YaccProduction):
        """in_methods : SCAN LPAREN RPAREN
                        | PRINT LPAREN clist RPAREN
                        | LIST LPAREN clist RPAREN
                        | LEN LPAREN clist RPAREN
                        | EXIT LPAREN clist RPAREN"""
        if len(p) == 4:          
            p[0] = FunctionCall(id=p[1], args=None, pos=getPosition(p))
        else:
            p[0] = FunctionCall(id=p[1], args=p[3], pos=getPosition(p))
    
    def p_expr(self, p: yacc.YaccProduction):
        '''expr : expr LSQUAREBR expr RSQUAREBR
            | LSQUAREBR clist RSQUAREBR
            | expr QUESTION expr COLON expr 
            | expr PLUS expr 
            | expr MINUS expr 
            | expr TIMES expr 
            | expr DIVIDE expr 
            | expr GREATER_THAN expr 
            | expr LESS_THAN expr 
            | expr EQUAL expr 
            | expr EQ expr 
            | expr GREATER_THAN_EQUAL_TO expr 
            | expr LESS_THAN_EQUAL_TO expr 
            | expr NOT_EQUAL expr 
            | expr OR expr 
            | expr AND expr 
            | NOT expr 
            | PLUS expr 
            | MINUS expr 
            | ID 
            | assignment
            | ID LPAREN clist RPAREN
            | NUMBER
            | in_methods
            | STRING'''
        if len(p) == 4 or len(p) == 3:
            if p[1] == '-':
                p[2].value = -p[2].value
            elif p[1] == '!':
                p[2].value = 0 if p[2].value else 1
            p[0] = p[2]
        else:
            if p.slice[1].type in ('NUMBER', 'STRING', 'ID'):
                p[0] = p.slice[1]
            else:
                p[0] = p[1]

    def p_expr_list(self, p: yacc.YaccProduction):
        '''expr_list : LSQUAREBR clist RSQUAREBR'''
        p[0] = p[2]

    def p_operation_on_list(self, p: yacc.YaccProduction):
        '''operation_on_list : expr LSQUAREBR expr RSQUAREBR
                            | ID LSQUAREBR expr RSQUAREBR'''
        p[0] = OperationOnList(expr=p[1], index_expr=p[3], pos=getPosition(p))

    def p_assignment(self, p: yacc.YaccProduction):
        '''assignment : ID EQ expr'''
        p[0] = Assignment(id=p[1], expr=p[3], pos=getPosition(p))
        
    def p_ternary_expr(self, p: yacc.YaccProduction):
        '''ternary_expr : expr QUESTION expr COLON expr  '''
        p[0] = TernaryExpr(cond=p[1], first_expr=p[3], second_expr=p[5], pos=getPosition(p))

    def p_function_call(self, p: yacc.YaccProduction):
        '''function_call : ID LPAREN clist RPAREN'''
        p[0] = FunctionCall(id=p[1], args=p[3], pos=getPosition(p))

    def p_function_call_error(self, p):
        '''function_call : ID LPAREN error RPAREN'''
        self.handle_error('function call', p[3])

    def p_binary_expr(self, p: yacc.YaccProduction):
        '''binary_expr : expr PLUS expr                   
                       | expr MINUS expr                  
                       | expr TIMES expr                  
                       | expr DIVIDE expr                 
                       | expr MOD expr                 
                       | expr GREATER_THAN expr
                        | expr GREATER_THAN_EQUAL_TO expr
                        | expr LESS_THAN expr
                        | expr LESS_THAN_EQUAL_TO expr
                        | expr EQ expr
                        | expr EQUAL expr
                        | expr NOT expr
                        | expr NOT_EQUAL expr
                        | expr OR expr
                        | expr AND expr'''
        p[0] = BinExpr(left=p[1], op=p[2], right=p[3], pos=getPosition(p))

    def p_empty(self, p: yacc.YaccProduction):
        '''empty :'''
        p[0] = []

    def handle_error(self, where, p):
        if not self.pre_parse:
            print(bcolors.FAIL + f'Syntax error' + f' at line {p.lineno}, column {self.scanner.find_token_column(p)}' +
                  bcolors.ENDC + f' in {where} with token {p}')

    def p_error(self, p):
        control_flags.parser_failed = True
        if p is not None:
            pass
        else:
            print('Unexpected end of input')