import logging
import os

import dotenv
from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout

from bitwarden_secrets_manager_python import BWS

from api_viewer.api import SpecRegistry, ClientRegistry
from api_viewer.api.request_handler import APIRequestHandler
from api_viewer.constants import NO_MARGIN
from api_viewer.emitter import signal_emitter
from api_viewer.log.decorator import log_method_calls

dotenv.load_dotenv()
logger =  logging.getLogger(__name__)


@log_method_calls()
class CentralChildWidget(QWidget):
    def __init__(self, parent=None, layout=None):
        super().__init__(parent)
        logger.debug(f"Initializing {self.__class__.__name__} with parent: {parent.__class__.__name__}")

        self.spec_registry = SpecRegistry()
        self.client_registry = ClientRegistry()
        self.secrets_manager = BWS(
            bws_access_token=os.getenv("BWS_ACCESS_TOKEN"),
            cache_duration=os.getenv("BWS_CACHE_DURATION", 600),
            bws_path=os.getenv("BWS_PATH", "../bws.exe"),
        )
        logger.debug(f"Initialized secrets manager: {self.secrets_manager.__class__.__name__}")

        self.signals = signal_emitter

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
