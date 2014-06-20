from collections import defaultdict

import AST
from Memory import *
from visit import *

# types: int, string, float

# ideas for optimisation:
# - use iinc instead of the pattern: iconst iload_1 iadd istore_1
# - get rid of series of goto's, like in if (condition) break;, we want to have one big jump
# enhancements:
# - implement nested breaks, continues - easy peasy :3
# - add argument to break, possibly continue - also easy
# - nested conditions ((a < b) || (c > d))?
# - ... for loop :P

PUSH_INT_CONST = ['iconst_m1', 'iconst_0', 'iconst_1', 'iconst_2', 'iconst_3', 'iconst_4', 'iconst_5']
PUSH_FLO_CONST = ['fconst_0', 'fconst_1', 'fconst_2']
PUSH_BYTE = 'bipush'
PUSH_SHORT = 'sipush'
PUSH_CONST = 'ldc'
PUSH_INT = 'iload'
PUSH_INT_N = ['iload_0', 'iload_1', 'iload_2', 'iload_3']
PUSH_FLO = 'fload'
PUSH_FLO_N = ['fload_0', 'fload_1', 'fload_2', 'fload_3']
PUSH_STR = 'aload'
PUSH_STR_N = ['aload_0', 'aload_1', 'aload_2', 'aload_3']
POP_INT = 'istore'
POP_INT_N = ['istore_0', 'istore_1', 'istore_2', 'istore_3']
POP_FLO = 'fstore'
POP_FLO_N = ['fstore_0', 'fstore_1', 'fstore_2', 'fstore_3']
POP_STR = 'astore'
POP_STR_N = ['astore_0', 'astore_1', 'astore_2', 'astore_3']
POP = 'pop'
POP2 = 'pop2'
DUP = 'dup'
ADD_INT = 'iadd'
ADD_FLO = 'fadd'
SUB_INT = 'isub'
SUB_FLO = 'fsub'
MUL_INT = 'imul'
MUL_FLO = 'fmul'
DIV_INT = 'idiv'
DIV_FLO = 'fdiv'
REM_INT = 'irem'
REM_FLO = 'frem'
NEG_INT = 'ineg'
NEG_FLO = 'fneg'
SHL_INT = 'ishl'
SHR_INT = 'ishr'
AND_INT = 'iand'
OR_INT = 'ior'
XOR_INT = 'ixor'
INC_INT = 'iinc'
INT2FLO = 'i2f'
FLO2INT = 'f2i'
COMP_FLO_LE = 'fcmpl'
COMP_FLO_GR = 'fcmpg'
IF_ZERO = 'ifeq'
IF_NOT_ZERO = 'ifne'
IF_NEGATIVE = 'iflt'
IF_NONNEGATIVE = 'ifge'
IF_POSITIVE = 'ifgt'
IF_NONPOSITIVE = 'ifle'
IF_INT_EQUAL = 'if_icmpeq'
IF_INT_NEQUAL = 'if_icmpne'
IF_INT_LESS = 'if_icmplt'
IF_INT_GEQUAL = 'if_icmpge'
IF_INT_GREATER = 'if_icmpgt'
IF_INT_LEQUAL = 'if_icmple'
IF_STR_EQUAL = 'if_acmpeq'
IF_STR_NEQUAL = 'if_acmpne'
GOTO = 'goto'

JUMP_INSTR = [COMP_FLO_LE, COMP_FLO_GR, IF_ZERO, IF_NOT_ZERO, IF_NEGATIVE, IF_NONNEGATIVE, IF_POSITIVE, IF_NONPOSITIVE,
              IF_INT_EQUAL, IF_INT_NEQUAL, IF_INT_LESS, IF_INT_GEQUAL, IF_INT_GREATER, IF_INT_LEQUAL, IF_STR_EQUAL,
              IF_STR_NEQUAL, GOTO]
RETURN_INT = 'ireturn'
RETURN_FLO = 'freturn'
RETURN_STR = 'areturn'
RETURN = 'return'

NEW = 'new'

PACKAGE_NAME = ""

STATIC_CALL = 'invokestatic'
SPECIAL_CALL = 'invokespecial'
VIRTUAL_CALL = 'invokevirtual'
INIT = '<init>()V'
GET_PRINT = 'getstatic java/lang/System/out Ljava/io/PrintStream;'
CALL_PRINT = VIRTUAL_CALL + ' java/io/PrintStream/println(Ljava/lang/String;)V'
STRING_BUILDER = 'java/lang/StringBuilder'
APPEND_PROTOTYPE = "append(Ljava/lang/String;)Ljava/lang/StringBuilder;"
TO_STRING_PROTOTYPE = "toString()Ljava/lang/String;"


class Function(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.code = []
        self.arguments = []
        self.variables = 0

    def addInstruction(self, instr):
        self.code.append(instr)

    def addArgument(self, arg):
        self.arguments.append(arg)
        self.variables += 1

class BInstruction(object):
    def __init__(self, cmd, arg=None):
        self.code = cmd
        self.arg = arg

    def tostring(self):
        argstr = '' if self.arg is None else str(self.arg)
        return "\t" + self.code + ' ' + argstr


class LabelInstruction(object):
    def __init__(self, name):
        self.name = name

    def tostring(self):
        return self.name + ":"


class Translator(object):
    def __init__(self):
        self.stack = MemoryStack(Memory('mem1'))
        self.labelno = 0
        self.lineno = 0
        self.functions = []

        self.operationCodes = defaultdict(lambda: defaultdict())
        self.relationCodes = defaultdict(lambda: defaultdict())
        self.loadStoreCodes = defaultdict(lambda: defaultdict())

        self.operationCodes['+']['float'] = ADD_FLO
        self.operationCodes['-']['float'] = SUB_FLO
        self.operationCodes['*']['float'] = MUL_FLO
        self.operationCodes['/']['float'] = DIV_FLO
        self.operationCodes['%']['float'] = REM_FLO

        self.operationCodes['+']['int'] = ADD_INT
        self.operationCodes['-']['int'] = SUB_INT
        self.operationCodes['*']['int'] = MUL_INT
        self.operationCodes['/']['int'] = DIV_INT
        self.operationCodes['%']['int'] = REM_INT

        self.operationCodes['&']['int'] = AND_INT
        self.operationCodes['^']['int'] = XOR_INT
        self.operationCodes['|']['int'] = OR_INT
        self.operationCodes['<<']['int'] = SHL_INT
        self.operationCodes['>>']['int'] = SHR_INT

        self.relationCodes['<']['int'] = IF_INT_LESS
        self.relationCodes['>']['int'] = IF_INT_GREATER
        self.relationCodes['<=']['int'] = IF_INT_LEQUAL
        self.relationCodes['>=']['int'] = IF_INT_GEQUAL
        self.relationCodes['==']['int'] = IF_INT_EQUAL
        self.relationCodes['!=']['int'] = IF_INT_NEQUAL

        self.relationCodes['<']['float'] = IF_NEGATIVE
        self.relationCodes['>']['float'] = IF_POSITIVE
        self.relationCodes['<=']['float'] = IF_NONPOSITIVE
        self.relationCodes['>=']['float'] = IF_NONNEGATIVE

        self.relationCodes['==']['string'] = IF_STR_EQUAL
        self.relationCodes['!=']['string'] = IF_STR_NEQUAL

        self.loadStoreCodes['store']['int'] = POP_INT
        self.loadStoreCodes['storen']['int'] = POP_INT_N

        self.loadStoreCodes['store']['float'] = POP_FLO
        self.loadStoreCodes['storen']['float'] = POP_FLO_N
        self.loadStoreCodes['store']['string'] = POP_STR
        self.loadStoreCodes['storen']['string'] = POP_STR_N

        self.loadStoreCodes['load']['int'] = PUSH_INT
        self.loadStoreCodes['loadn']['int'] = PUSH_INT_N
        self.loadStoreCodes['load']['float'] = PUSH_FLO
        self.loadStoreCodes['loadn']['float'] = PUSH_FLO_N
        self.loadStoreCodes['load']['string'] = PUSH_STR
        self.loadStoreCodes['loadn']['string'] = PUSH_STR_N

    def callPrint(self, type):
        return 'invokevirtual java/io/PrintStream/println(' + self.getShortTypeName(type) + ')V'

    def getShortTypeName(self, type):
        return type[0].upper() if type != "string" else "Ljava/lang/String;"

    def getMethodNameArgs(self, function):
        args = "".join([self.getShortTypeName(i) for i in
                        function.arguments]) if function.name != "main" else "[Ljava/lang/String;"
        return function.name + "(" + args + ")" + self.getShortTypeName(function.type)

    def getMethodForCall(self, name):
        function = filter(lambda x: x.name == name, self.functions)[0]
        return PACKAGE_NAME + "Main/" + self.getMethodNameArgs(function)

    def printInstruction(self, instr, arg=None):  # non-jump instruction
        binstr = BInstruction(instr, arg)
        self.functions[-1].addInstruction(binstr)

    def printLabel(self, name):
        self.functions[-1].addInstruction(LabelInstruction(name))

    def printJump(self, instr, label):
        binstr = BInstruction(instr, label)
        self.functions[-1].addInstruction(binstr)

    def printCommands(self, file):
        out = open(file, "w")

        out.write(".class public Main\n")
        out.write(".super java/lang/Object\n")

        for function in self.functions:
            out.write(".method public static " + self.getMethodNameArgs(function) + "\n")
            out.write(".limit stack 5\n")
            out.write(".limit locals " + str(function.variables) + "\n")
            for cmd in function.code:
                out.write(cmd.tostring() + "\n")
            out.write(".end method\n\n")
        out.close()

    def getLabelName(self):
        name = "Label" + str(self.labelno)
        self.labelno += 1
        return name

    def storeTopOfStack(self, name):
        lookup = self.stack.lookup(name)
        type = lookup[0]
        index = lookup[1]
        if index < 4:
            code = self.loadStoreCodes['storen'][type][index]
        else:
            code = self.loadStoreCodes['store'][type]
        self.printInstruction(code, str(index) if index >= 4 else None)

    def loadOntoStack(self, name):
        lookup = self.stack.lookup(name)
        type = lookup[0]
        index = lookup[1]
        if index < 4:
            code = self.loadStoreCodes['loadn'][type][index]
        else:
            code = self.loadStoreCodes['load'][type]
        self.printInstruction(code, str(index) if index >= 4 else None)

        # prints the comparison instruction, appropriate to type and operation, and
        # a jump to the label
    def makeComparisonAndJump(self, type, operation, label):
        if type == "float":
            op = COMP_FLO_GR if operation[0] == '>' else COMP_FLO_LE
            self.printInstruction(op)
        self.printJump(self.relationCodes[operation][type], label)

    # this is ugly, but the Java compiler does this similarly
    def printOperation(self, operation, type):
        if type == 'string' and operation == '+':
            self.stack.register("___string1", "string")
            self.stack.register("___string2", "string")
            self.storeTopOfStack("___string1")
            self.storeTopOfStack("___string2")
            self.printInstruction(NEW, STRING_BUILDER)
            self.printInstruction(DUP)
            self.printInstruction(SPECIAL_CALL, STRING_BUILDER + "/" + INIT)
            self.loadOntoStack("___string2")
            self.printInstruction(VIRTUAL_CALL, STRING_BUILDER + "/" + APPEND_PROTOTYPE)
            self.loadOntoStack("___string1")
            self.printInstruction(VIRTUAL_CALL, STRING_BUILDER + "/" + APPEND_PROTOTYPE)
            self.printInstruction(VIRTUAL_CALL, STRING_BUILDER + "/" + TO_STRING_PROTOTYPE)
        else:
            self.printInstruction(self.operationCodes[operation][type])


    @on('node')
    def visit(self, node):
        pass


    @when(AST.Program)
    def visit(self, node):
        node.fundefs.accept(self)
        self.functions.append(Function("main", "void"))
        node.declarations.accept(self)
        node.instructions.accept(self)
        self.printInstruction(RETURN)

    @when(AST.DeclarationList)
    def visit(self, node):
        for declaration in node.declarations:
            declaration.accept(self)

    @when(AST.Declaration)
    def visit(self, node):
        self.currType = node.type
        node.inits.accept(self)

    @when(AST.InitList)
    def visit(self, node):
        for init in node.inits:
            init.accept(self)


    @when(AST.Init)
    def visit(self, node):
        value = node.expr.accept(self)  # compute the expression
        index = self.stack.register(node.id, self.currType)
        self.functions[-1].variables += 1
        self.storeTopOfStack(node.id)  # put what we have on top of stack in the index

    @when(AST.InstructionList)
    def visit(self, node):
        for instr in node.instructions:
            instr.accept(self)


    @when(AST.PrintInstr)
    def visit(self, node):
        self.printInstruction(GET_PRINT)
        type = node.expr.accept(self)  # get the result of expression on the stack
        self.printInstruction(self.callPrint(type))

    @when(AST.LabeledInstr)  # pointless...
    def visit(self, node):
        label = self.getLabelName()
        self.printLabel(label)
        node.instr.accept(self)


    @when(AST.Assignment)
    def visit(self, node):
        node.expr.accept(self)
        self.storeTopOfStack(node.id)


    # we assume the condition will always be inside if, not another expression or condition
    # because otherwise we don't have a way to store the intermediate boolean values (no bool :#)
    @when(AST.ChoiceInstr)
    def visit(self, node):
        if (node.elseclause == None):
            type = node.ifclause.accept(self)  # two sides of the relation are on the stack
            thenend = self.getLabelName()
            thenstart = self.getLabelName()
            self.makeComparisonAndJump(type, node.ifclause.op, thenstart)
            self.printJump(GOTO, thenend)
            self.printLabel(thenstart)
            node.thenclause.accept(self)
            self.printLabel(thenend)
        else:
            type = node.ifclause.accept(self)
            thenstart = self.getLabelName()
            thenend = self.getLabelName()
            elsestart = self.getLabelName()
            elseend = self.getLabelName()

            self.makeComparisonAndJump(type, node.ifclause.op, thenstart)
            self.printJump(GOTO, elsestart)
            self.printLabel(thenstart)
            node.thenclause.accept(self)
            self.printJump(GOTO, elseend)
            self.printLabel(elsestart)
            node.elseclause.accept(self)
            self.printLabel(elseend)


    @when(AST.WhileInstr)
    def visit(self, node):
        start = self.getLabelName()
        end = self.getLabelName()
        condition = self.getLabelName()
        self.breakLabel = end
        self.continueLabel = condition

        # shorter, but has jump in the beginning and condition at the end :)
        # self.printJump(GOTO, condition)
        # self.printLabel(start)
        # node.instruction.accept(self)
        # self.printLabel(condition)
        # type = node.condition.accept(self)
        # self.makeComparisonAndJump(type, node.condition.op , start)
        # self.printLabel(end)

        # longer, but more natural
        self.printLabel(condition)
        type = node.condition.accept(self)
        self.makeComparisonAndJump(type, node.condition.op, start)
        self.printJump(GOTO, end)
        self.printLabel(start)
        node.instruction.accept(self)
        self.printJump(GOTO, condition)
        self.printLabel(end)


    @when(AST.ReturnInstr)
    def visit(self, node):
        type = None
        if node.expression is not None:
            type = node.expression.accept(self)
        if type == 'int' and self.functions[-1].type == 'int':
            self.printInstruction(RETURN_INT)
        elif type == 'float' and self.functions[-1].type == 'float':
            self.printInstruction(RETURN_FLO)
        elif type == 'int' and self.functions[-1].type == 'float':
            self.printInstruction(INT2FLO)
            self.printInstruction(RETURN_FLO)
        elif type == 'float' and self.functions[-1].type == 'int':
            self.printInstruction(FLO2INT)
            self.printInstruction(RETURN_FLO)
        else:
            self.printInstruction(RETURN_STR)


    @when(AST.ContinueInstr)
    def visit(self, node):
        self.printJump(GOTO, self.continueLabel)


    @when(AST.BreakInstr)
    def visit(self, node):
        self.printJump(GOTO, self.breakLabel)


    @when(AST.CompoundInstr)
    def visit(self, node):
        if node.declarations is not None:
            node.declarations.accept(self)
        if node.instructions is not None:
            node.instructions.accept(self)


    @when(AST.ExpressionList)
    def visit(self, node):
        for expr in node.expressions:
            expr.accept(self)


    @when(AST.BinExpr)
    def visit(self, node):
        rtype = node.left.accept(self)
        ltype = node.right.accept(self)
        if (ltype == rtype):
            self.printOperation(node.op, ltype)
            return ltype
        elif (ltype == 'int' and rtype == 'float') or (rtype == 'int' and ltype == 'float'):
            self.printOperation(node.op, 'int')
            return 'int'
        else:
            print 'error - wrong types'


    @when(AST.RelExpr)
    def visit(self, node):  # push the two sides onto the stack, surrounding if will make the comparison and jump
        rtype = node.left.accept(self)
        ltype = node.right.accept(self)
        if (ltype == rtype):
            return ltype
        elif (ltype == 'int' and rtype == 'float') or (rtype == 'int' and ltype == 'float'):
            return 'int'
        else:
            print 'error - wrong types' + ltype + ' ' + rtype


    @when(AST.GroupingExpr)
    def visit(self, node):
        return node.inside.accept(self)


    @when(AST.FunCallExpr)
    def visit(self, node):
        if (node.inside != None):
            # push the arguments onto the stack
            for expr in node.inside.expressions:
                expr.accept(self)
        function = filter(lambda x: x.name == node.id, self.functions)[0]
        self.printInstruction(STATIC_CALL, self.getMethodForCall(node.id))
        return function.type

    @when(AST.Const)
    def visit(self, node):
        return node.value.accept(self)


    @when(AST.Integer)
    def visit(self, node):
        val = int(node.value)
        if 6 > val > -2:
            self.printInstruction(PUSH_INT_CONST[val + 1])
        elif -129 < val < 128:
            self.printInstruction(PUSH_BYTE, node.value)
        else:
            self.printInstruction(PUSH_SHORT, node.value)
        return 'int'


    @when(AST.Float)
    def visit(self, node):  # todo use the fconst_0-2 codes
        self.printInstruction(PUSH_CONST, node.value)
        return 'float'


    @when(AST.String)
    def visit(self, node):
        self.printInstruction(PUSH_CONST, node.value)
        return 'string'


    @when(AST.Variable)
    def visit(self, node):
        lookup = self.stack.lookup(node.value)
        self.loadOntoStack(node.value)
        return lookup[0]

    @when(AST.FunDefList)
    def visit(self, node):
        for fundef in node.fundefs:
            fundef.accept(self)

    @when(AST.FunDef)
    def visit(self, node):
        function = Function(node.id, node.type)
        self.functions.append(function)
        self.addArguments(node.args)
        self.stack.push(Memory('mem1'))
        node.args.accept(self)
        node.comp_instrs.accept(self)
        self.stack.pop()

    @when(AST.ArgumentList)
    def visit(self, node):
        for arg in node.args:
            arg.accept(self)

    @when(AST.Argument)
    def visit(self, node):
        self.stack.register(node.id, node.type)


    def addArguments(self, arglist):
        for arg in arglist.args:
            self.functions[-1].addArgument(arg.type)
