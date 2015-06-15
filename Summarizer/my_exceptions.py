class ArgumentParserException(Exception):
    """ ArgumentParserException to raise when context-dependent required argument is not present. """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "This argument is required: " + repr(self.value)
