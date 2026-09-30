"""Exception classes in PAGOS."""


class NoUnitsToConvertError(Exception):
    """Exception raised when trying to call .to() on something without units."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ConversionError(Exception):
    """Exception raised when attempting an invalid conversion."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DifferentGasesError(Exception):
    """Exception raised when attempting a conversion between quantities representing two different gases."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
