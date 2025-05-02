from api_viewer.log.decorator import log_method_calls


@log_method_calls()
class SpecAddress:
    """
    SpecAddress is a class that represents an uri to an api specification.
    It is used to identify the location of the api specification.
    It can be a local file path or a remote URL.

    Attributes:
        _raw (str): The raw string representation of the spec address.

    Methods:
        __init__(spec_address: str) -> None:
            Initializes the SpecAddress with a raw string.

        __str__() -> str:
            Returns the raw string representation of the spec address.
    """
    def __init__(self, spec_address: str) -> None:
        if not isinstance(spec_address, str):
            raise ValueError(f"SpecAddress must be a string, got {type(spec_address)}")

        self._raw = spec_address

    def __str__(self):
        return self._raw
