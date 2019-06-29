import abc

class Command(abc.ABC):
    def __init__(self, config, args):
        self.config = config
        self.args = args

    @abc.abstractmethod
    def run(self):
        pass