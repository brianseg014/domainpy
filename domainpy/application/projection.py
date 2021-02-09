
class Projection:

    def __handle__(self, e):
        # Compat with bus
        self.__project__(e)

    def __project__(self, e):
        self.project(e)

    def project(self, e):
        pass
