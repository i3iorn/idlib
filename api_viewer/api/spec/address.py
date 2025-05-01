class SpecAddress:
    def __init__(self, spec_address: str) -> None:
        if not isinstance(spec_address, str):
            raise ValueError

        self._raw = spec_address

    def __str__(self):
        return self._raw
