class Node(object):
    def __str__(self):
        pass

    def accept(self, visitor):
        return visitor.visit(self)


class ExpressionList(Node):
    def __init__(self):
        self.expressions = []

    def addExpr(self, expr):
        self.expressions.append(expr)


class Expression(Node):
    pass


class BinExpr(Expression):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class RelExpr(Expression):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class GroupingExpr(Expression):
    def __init__(self, inside):
        self.inside = inside


class FunCallExpr(Expression):
    def __init__(self, id, inside):
        self.id = id
        self.inside = inside


class Const(Expression):
    def __init__(self, value):
        self.value = value


class Integer(Const):
    def __init__(self, value):
        self.value = value


class Float(Const):
    def __init__(self, value):
        self.value = value


class String(Const):
    def __init__(self, value):
        self.value = value


class Variable(Node):
    def __init__(self, value):
        self.value = value


class Argument(Node):
    def __init__(self, type, id):
        self.type = type
        self.id = id


class ArgumentList(Node):
    def __init__(self):
        self.args = []

    def add_argument(self, arg):
        self.args.append(arg)


class FunDefList(Node):
    def __init__(self):
        self.fundefs = []

    def addDef(self, fundef):
        self.fundefs.append(fundef)


class FunDef(Node):
    def __init__(self, type, id, args, comp_instrs):
        self.type = type
        self.id = id
        self.args = args
        self.comp_instrs = comp_instrs


class DeclarationList(Node):
    def __init__(self):
        self.declarations = []

    def addDecl(self, decl):
        self.declarations.append(decl)


class Declaration(Node):
    def __init__(self, type, inits):
        self.type = type
        self.inits = inits


class InitList(Node):
    def __init__(self):
        self.inits = []

    def addInit(self, init):
        self.inits.append(init)


class Init(Node):
    def __init__(self, id, expr):
        self.id = id
        self.expr = expr


class InstructionList(Node):
    def __init__(self):
        self.instructions = []

    def addInstr(self, instr):
        self.instructions.append(instr)


class Instruction(Node):
    pass


class PrintInstr(Instruction):
    def __init__(self, expr):
        self.expr = expr


class LabeledInstr(Instruction):
    def __init__(self, id, instr):
        self.id = id
        self.instr = instr


class Assignment(Instruction):
    def __init__(self, id, expr):
        self.id = id
        self.expr = expr


class ChoiceInstr(Instruction):
    def __init__(self, ifclause, thenclause, elseclause=None):
        self.ifclause = ifclause
        self.thenclause = thenclause
        self.elseclause = elseclause


class WhileInstr(Instruction):
    def __init__(self, condition, instruction):
        self.condition = condition
        self.instruction = instruction


class RepeatInstr(Instruction):
    def __init__(self, instructions, condition):
        self.instructions = instructions
        self.condition = condition


class ReturnInstr(Instruction):
    def __init__(self, expression):
        self.expression = expression


class ContinueInstr(Instruction):
    pass


class BreakInstr(Instruction):
    pass


class CompoundInstr(Instruction):
    def __init__(self, declarations, instructions):
        self.declarations = declarations
        self.instructions = instructions


class Program(Node):
    def __init__(self, declarations, fundefs, instructions):
        self.declarations = declarations
        self.fundefs = fundefs
        self.instructions = instructions
