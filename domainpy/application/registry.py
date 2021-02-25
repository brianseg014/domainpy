

class Registry:
    
    def __init__(self):
        self.components = {}

    def has(self, key):
        return key in self.components

    def assert_component(self, key):
        assert self.has(key)

    def put(self, key, value):
        self.components[key] = value

    def get(self, key):
        return self.components[key]
    