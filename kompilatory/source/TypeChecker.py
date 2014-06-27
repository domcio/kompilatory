#!/usr/bin/python

from collections import defaultdict
from SymbolTable import SymbolTable, VariableSymbol, FunctionSymbol

class TypeChecker(object):

    ttype = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))
    def __init__(self):
        self.table = SymbolTable(None, "root")
        self.currType = "" # int a = 2, b = 3, c = 4 -> currType holds "int"
        
    for op in ['+', '-', '*', '/', '%', '<', '>', '<<', '>>', '|', '&', '^', '<=', '>=', '==', '!=']:
        for type in ['int', 'float', 'string']:
            # 'na' is a special 'unknown' type, which is a result of invalid operation, but
            # is itself a valid operation, no matter the operands.
            # This is so that one mistake in an expression doesn't propagate, resulting 
            # in too many error messages.
            # E.g. in the initialization: float a = 1.2 + "dfd"/2;, right-hand side will evaluate to 
            # float + na, which is na, but "a" will be resolved to float, so that
            # further references to "a" will ignore the error.
            # This also applies to assignments and function call expressions 
            # (fun(1, 1.2%"str") for fun(int, int) will produce one error. 
            ttype[op][type]['na'] = 'na'
            ttype[op]['na'][type] = 'na'
            ttype[op]['na']['na'] = 'na'
        
    for op in ['+', '-', '*', '/', '%', '<', '>', '<<', '>>', '|', '&', '^', '<=', '>=', '==', '!=']:
        ttype[op]['int']['int'] = 'int'
    
    for op in ['+', '-', '*', '/']:
        ttype[op]['int']['float'] = 'float'
        ttype[op]['float']['int'] = 'float'
        ttype[op]['float']['float'] = 'float'
        
    for op in ['<', '>', '<=', '>=', '==', '!=']:
        ttype[op]['int']['float'] = 'int'
        ttype[op]['float']['int'] = 'int'
        ttype[op]['float']['float'] = 'int'
    
    ttype['+']['string']['string'] = 'string'
    ttype['*']['string']['int'] = 'string'

    for op in ['<', '>', '<=', '>=', '==', '!=']:
        ttype[op]['string']['string'] = 'int'
    
    def visit_Program(self, node):
        node.declarations.accept(self)
        node.fundefs.accept(self)
        node.instructions.accept(self)
        
    def visit_DeclarationList(self, node):
        for declaration in node.declarations:
            declaration.accept(self)
            
    def visit_Declaration(self, node):
        self.currType = node.type
        node.inits.accept(self)
        self.currType = ""
        
    def visit_InitList(self, node):
        for init in node.inits:
            init.accept(self)
            
    def visit_Init(self, node):
        initType = node.expr.accept(self)
        if initType == 'na' or initType == self.currType or (initType == "int" and self.currType == "float"):
            if self.table.get(node.id) is not None: # we only look in the innermost scope
                print "Redefinition of a variable or a function '{}' in line {}".format(node.id, node.lineno)
            else:
                self.table.put(node.id, VariableSymbol(node.id, self.currType))
        else:
            print "Illegal operation in line {} - cannot assign '{}' to '{}'".format(node.lineno, initType, self.currType)
    
    def visit_FunDefList(self, node):
        for funDef in node.fundefs:
            funDef.accept(self)
            
    def visit_FunDef(self, node):
        if self.table.get(node.id) is not None:
            print "Redefinition of a variable or function '{}' in line {}".format(node.id, node.lineno)
        else:
            funcSym = FunctionSymbol(node.id, node.type, SymbolTable(self.table, node.id))
            self.table.put(node.id, funcSym)
            self.currentFunction = funcSym # needed for gathering the function parameters, as well as visiting its body
            self.table = self.currentFunction.table
            if node.args is not None:
                node.args.accept(self) # add parameters to the scope of the function
            node.comp_instrs.accept(self) # visit the body of function
            self.table = self.table.getParentScope() # return to outer scope
            self.currentFunction = None
            
    def visit_ArgumentList(self, node):
        for argument in node.args:
            argument.accept(self)
        # for later invocations, FunctionVariable currentFunction has information about its parameters
        # (since we lose the reference to the scope of its body as soon as we exit it)
        self.currentFunction.countParams()   
            
    def visit_Argument(self, node):
        if self.table.get(node.id) is not None:
            print "Redeclaration of argument '{}' in line {}".format(node.id, node.lineno)
        else:
            self.table.put(node.id, VariableSymbol(node.id, node.type))
            
    def visit_CompoundInstr(self, node): # if we are in a function body, new scope is made inside the already existing scope with parameters
        newScope = SymbolTable(self.table, "unnamed")
        self.table = newScope
        if node.declarations is not None:
            node.declarations.accept(self)
        node.instructions.accept(self)
        self.table = self.table.getParentScope() # return to the surrounding scope
    
    def visit_InstructionList(self, node):
        for instruction in node.instructions:
            instruction.accept(self)
            
    def visit_PrintInstr(self, node):
        exprType = node.expr.accept(self)
        
    def visit_LabeledInstr(self, node):
        node.instr.accept(self)
        
    def visit_Assignment(self, node):
        symbol = self.table.getRecursive(node.id)
        rhstype = node.expr.accept(self)
        if symbol is None: # look in the current scope as well as its predecessors
            print "Undefined variable '{}' in line {}".format(node.id, node.lineno)
        elif rhstype != 'na' and symbol.type != rhstype and (symbol.type != "float" or rhstype != "int"):
            print "Illegal operation in line {} - cannot assign '{}' to '{}'".format(node.lineno, rhstype, symbol.type)
        
    def visit_ChoiceInstr(self, node):
        node.ifclause.accept(self)
        node.thenclause.accept(self)
        if node.elseclause is not None:
            node.elseclause.accept(self)
    
    def visit_WhileInstr(self, node):
        node.condition.accept(self)
        node.instruction.accept(self)

    def visit_RepeatInstr(self, node):
        node.instructions.accept(self)        
        node.condition.accept(self)
    
    def visit_ReturnInstr(self, node):
        if self.currentFunction is None:    
            print "Return statement outside of a function body, line {}".format(node.lineno)
        else:
            returnType = node.expression.accept(self)
            if (returnType != "na") and (returnType != self.currentFunction.type) and (returnType != 'int' or self.currentFunction.type != 'float'):
                print "Invalid return type in line {}; should be '{}'".format(node.lineno, self.currentFunction.type)
            
    def visit_ContinueInstr(self, node):
        pass
        
    def visit_BreakInstr(self, node):
        pass
    
    def visit_BinExpr(self, node):
        type1 = node.left.accept(self)
        type2 = node.right.accept(self)
        op    = node.op;
        if TypeChecker.ttype[op][type1][type2] is None:
            print "Invalid operands of '{}' in line {}".format(node.op, node.lineno)
            return "na"
        else:
            return TypeChecker.ttype[op][type1][type2]
        
    def visit_GroupingExpr(self, node):
        return node.inside.accept(self)
        
    def visit_FunCallExpr(self, node):
        symbol = self.table.getRecursive(node.id)
        if (symbol is None) or isinstance(symbol, VariableSymbol):
            print "Undefined function '{}' in line {}".format(node.id, node.lineno)
            return 'na'
        else:
            if node.inside is None and symbol.params != []:
                print "Wrong number of arguments provided to function '{}' in line {}; should be {}".format(node.id, node.lineno, len(symbol.params))
            else:
                argTypes = [x.accept(self) for x in node.inside.expressions]
                paramTypes = symbol.params
                if len(argTypes) != len(paramTypes):
                    print "Wrong number of arguments provided to function '{}' in line {}; should be {}".format(node.id, node.lineno, len(paramTypes))
                else:
                    for a, p in zip(argTypes, paramTypes):
                        if (a != p) and (a != "int" or p != "float") and (a != 'na'):
                            print "Wrong type of one or more arguments in call to '{}' in line {}\n Correct argument types: {}".format(node.id, node.lineno, \
                                ", ".join(paramTypes))
            return symbol.type
        
    def visit_Integer(self, node):
        return 'int'
        
    def visit_Float(self, node):
        return 'float'
    
    def visit_String(self, node):
        return 'string'
        
    def visit_Variable(self, node):
        symbol = self.table.getRecursive(node.id)
        if symbol is None:
            print "Undefined variable '{}' in line {}".format(node.id, node.lineno)
            return "na"
        else:
            return symbol.type