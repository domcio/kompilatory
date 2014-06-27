#!/usr/bin/python

class Symbol():
    pass
    
class FunctionSymbol(Symbol):
    def __init__(self, name, type, table):
        self.name = name
        self.type = type
        self.params = []
        self.table = table
        
    def countParams(self):
        # extract parameters types from table
        self.params = [x.type for x in self.table.table]
        
class VariableSymbol(Symbol):
    def __init__(self, name, type):
        self.name = name
        self.type = type
    
class SymbolTable(object):
    def __init__(self, parent, name):
        self.table = []
        self.parent = parent

    def put(self, name, symbol):
        self.table.append(symbol)
    
    def get(self, name):
        search = filter((lambda x: x.name == name), self.table)
        return None if len(search)==0 else search[0]
    
    def getRecursive(self, name):
        if self.get(name) is None:
            return None if self.parent is None else self.parent.getRecursive(name)
        else:
            return self.get(name)
    
    def getParentScope(self):
        return self.parent