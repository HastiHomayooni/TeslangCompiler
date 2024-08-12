from TeslangParser import TeslangParser
import logging
import sys
import ply.yacc as yacc
from preParser import PreParser
import counters
import control_flags
import os
from colors import bcolors



def up_and_run_compiler():
    counters.init()
    control_flags.init()
    control_flags.lexer_failed = False
    control_flags.parser_failed = False
    control_flags.semantic_failed = False
    def start(pre_parse, table=None, ir_generation=False):
        tParser = TeslangParser(pre_parse=pre_parse)
        parser = yacc.yacc(module=tParser, debug=True, write_tables=True)
        ast = parser.parse(data, lexer=tParser.scanner)
        if ir_generation:
            table = ast.accept_ir_generation(table)
        else:
            table = ast.accept(pre_parse=pre_parse, table=table if not pre_parse else None)
        if pre_parse:
            PreParser().push_builtins_to_table(table)
        if not ir_generation and not pre_parse:
            table.show_unused_warning()
        return table
    table = start(pre_parse=True)
    table = start(pre_parse=False, table=table)
    compile_failed = control_flags.lexer_failed or control_flags.parser_failed or control_flags.semantic_failed
    if not compile_failed:
        start(pre_parse=False, ir_generation=True, table=table)
    else:
        print("\n\nCompilation failed and IR generation was not attempted.")

logging.basicConfig(
    level = logging.DEBUG,
    filename = "parselog.txt",
    filemode = "w",
    format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

data = open("input.txt", 'r').read()

up_and_run_compiler()

print()







# from TeslangLexer import TeslangLexer


# # Instantiate the lexer
# lexer = TeslangLexer()
# lexer.build()

# # Sample Teslang code
# teslang_code = '''
# fn main() {
#     print("Hello, Teslang!")
# }
# '''

# # Pass the Teslang code to the lexer
# lexer.input(teslang_code)

# # Tokenize and print the tokens
# while True:
#     tok = lexer.token()
#     if not tok:
#         break  # No more input
#     print(tok)