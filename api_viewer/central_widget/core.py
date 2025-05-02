import logging

from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout

from bwclient import get_bw_client

from api_viewer.api import SpecRegistry, ClientRegistry
from api_viewer.api.request_handler import APIRequestHandler
from api_viewer.constants import NO_MARGIN
from api_viewer.emitter import SignalEmitter
from api_viewer.log.decorator import log_method_calls

logger =  logging.getLogger(__name__)


@log_method_calls()
class CentralChildWidget(QWidget):
    def __init__(self, parent=None, layout=None):
        super().__init__(parent)
        logger.debug(f"Initializing {self.__class__.__name__} with parent: {parent.__class__.__name__}")

        self.spec_registry = SpecRegistry()
        self.client_registry = ClientRegistry()
        self.secrets_manager = get_bw_client()
        self.signals = SignalEmitter()

        self.api_handler = APIRequestHandler(self.secrets_manager, self.signals)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setObjectName(self.__class__.__name__)
        if layout is None:
            layout = QVBoxLayout()
        layout.setContentsMargins(*NO_MARGIN)
        self.setLayout(layout)

        if hasattr(self, "_setup_ui"):
            self._setup_ui()

        if hasattr(self, "_connect_signals"):
            self._connect_signals()

        if hasattr(self, "_load_settings"):
            self._load_settings()

        logger.debug(f"Finished initializing {self.__class__.__name__}")
