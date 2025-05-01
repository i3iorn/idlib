from api_viewer.api.protocol import Protocol
from api_viewer.api.spec.address import SpecAddress


class SpecReader:
    def __init__(self, spec_address: str) -> None:
        self._address = SpecAddress(spec_address)
        self._protocol = Protocol.from_spec_address(self._address)
        self._handler = self._protocol.handler_class(
            str(self._address),
            self._protocol.function,
            self._protocol.params,
            self._protocol.read_method
        )

    def read(self) -> str:
        return self._handler.read()
