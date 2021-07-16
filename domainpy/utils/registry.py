import typing 

from domainpy.exceptions import RegistryComponentNotFound


class Registry:
    
    def __init__(self):
        self.components = dict[type, typing.Any]()

    def has(self, key: type) -> bool:
        return key in self.components

    def assert_component(self, key: type):
        assert self.has(key)

    def put(self, key: type, value: typing.Any):
        self.components[key] = value

    def get(self, key):
        try:
            return typing.cast(key, self.components[key])
        except KeyError as e:
            raise RegistryComponentNotFound(
                f'instance for {key} not registered'
            )
    