

class Memory:
    def __init__(self, name): # memory name
        self.memory = [None for x in xrange(0, 256)]
        self.variables = 0
        
    def register(self, name, type):
        registeredNames = map(lambda x: x[0], filter(lambda x: x is not None, self.memory))
        if name in registeredNames:
            print 'error - redeclaration of variable'
        if self.variables == 256:
            print 'error - not enough space for new variable'
        index = self.memory.index(None)
        self.memory[index] = (name, type)
        return index
        
    def lookup(self, name):
        if not self.has_key(name):
            print 'error - no variable with that name'
        registeredNames = map(lambda x: x[0], filter(lambda x: x is not None, self.memory))
        index = registeredNames.index(name)
        return self.memory[index][1], index  # (type, index)
        
    def has_key(self, name):
        return name in map(lambda x: x[0], filter(lambda x: x is not None, self.memory))
        
class MemoryStack:
    
    def __init__(self, memory=None): # initialize memory stack with memory <memory>
        self.functions = []
        self.constants = []
        self.stack = []
        if memory is not None:
            self.stack.append(memory)
    
    def register(self, name, type):
        return self.stack[-1].register(name, type)
        
    def lookup(self, name):
        for memory in reversed(self.stack):
            if memory.has_key(name):
                return memory.lookup(name)
    
    def push(self, memory):
        self.stack.append(memory)
    
    def pop(self):
        return self.stack.pop()
        