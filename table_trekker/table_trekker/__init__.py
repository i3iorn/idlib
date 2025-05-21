import sys
from pathlib import Path
from time import sleep

sleep(5)

# Add the parent directory to the system path
sys.path.append(str(Path(__file__).resolve().parent.parent))
sleep(5)
# Setup custom logging
from table_trekker.log import initialize_logging

logger, log_emitter = initialize_logging(use_json=True)
sleep(5)
from table_trekker.utils import qt_exception_hook
sys.excepthook = qt_exception_hook

from table_trekker.file_interface.handler import FileInterfaceHandlerRegistry
from table_trekker.file_interface.interfaces.xlsx import ExcelInterface
from table_trekker.policy.core import Policy

def run():

    FileInterfaceHandlerRegistry.register(
        format_name="xlsx",
        handler_cls=ExcelInterface
    )

    Policy(
        title="KundID 1 Handling",
        description="What column should we put KundID 1 in?",
        options=[
            {"name": "REFERENCE", "description": "Place the KundID 1 in the reference field"},
            {"name": "CATEGORY", "description": "Place the KundID 1 in the category field"},
            {"name": "IGNORE", "description": "Ignore the KundID 1"},
        ]
    )
    Policy(
        title="KundID 2 Handling",
        description="What column should we put KundID 2 in?",
        options=[
            {"name": "REFERENCE", "description": "Place the KundID 2 in the reference field"},
            {"name": "CATEGORY", "description": "Place the KundID 2 in the category field"},
            {"name": "IGNORE", "description": "Ignore the KundID 2"},
        ]
    )

    Policy(
        title="Duplicate Handling",
        description="How should we handle duplicate organisation numbers?",
        options=[
            {"name": "STACK", "description": "Stack the duplicates in respective fields"},
            {"name": "REPLACE", "description": "Keeps the last duplicate"},
            {"name": "IGNORE", "description": "Keeps the first duplicate"}
        ]
    )
    """
    Policy(
        title="Error Handling",
        options=[
            {"name": "LOG", "description": "Log the error but continue."},
            {"name": "RAISE", "description": "Raise an exception and stop the process."},
            {"name": "IGNORE", "description": "Ignore the error and continue."}
        ]
    )
    """
    Policy(
        title="Grouping",
        description="How should we group the pages (ie Sheets in excel)?",
        options=[
            {"name": "ONE_TO_ONE", "description": "Each page in the input will have one file in the output.",
             "display": "One to One"},
            {"name": "MERGE_BY_FILE", "description": "One file in one file out.", "display": "Merge by file"},
            {"name": "MERGE_ALL", "description": "All pages in the input will be merged into one file in the output.",
             "display": "Merge All"},
            {"name": "GROUP_BY_MAIN_CODE", "description": "Group by main code (IE 4 characters).",
             "display": "Group by 4 letter code"},
            {"name": "GROUP_BY_SUB_CODE", "description": "Group by full kundkod.", "display": "Group by 7 letter code"},
            # {"name": "GROUP_BY_CATEGORY", "description": "Group by value in category field.", "display": "Group by Category"},
        ]
    )

    # Create a QApplication instance
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.log_emitter = log_emitter

    # Setup internationalization
    from table_trekker.internationalization import setup_internationalization
    translator = setup_internationalization("en_US")
    if translator:
        # Install the translator to the application
        app.installTranslator(translator)

    # Import the main application module
    from table_trekker.gui.window import ApplicationWindow

    # Create and show the main window
    window = ApplicationWindow(app)
    sys.exit(app.exec())
