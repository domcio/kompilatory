import sys

import ply.yacc as yacc

from Cparser import Cparser
from Translator import Translator
from source.TypeChecker import TypeChecker


if __name__ == '__main__':

    filename = None
    try:
        filename = sys.argv[1] if len(sys.argv) > 1 else "../resources/example.txt"
        input_file = open(filename, "r")
    except IOError:
        print("Cannot open {0} file".format(filename))
        sys.exit(0)

    Cparser = Cparser()
    parser = yacc.yacc(module=Cparser)
    text = input_file.read()
    
    ast = parser.parse(text, lexer=Cparser.scanner)

    translator = Translator()
    # ast.accept2(TypeChecker())
    ast.accept(translator)
    translator.print_commands(sys.argv[2] if len(sys.argv) > 2 else "../out/Main.j")