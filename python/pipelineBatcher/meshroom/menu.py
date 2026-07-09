"""
Add a menu for prod tools.
"""

# ========== Py standard lib imports ==========
import os
import logging
from pathlib import Path

# ========== External libraries ==========
# from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlComponent
from PySide6.QtCore import QUrl

# ========== Meshroom imports ==========
from meshroom.api import register_menu, Menu, MenuCallback, registerQmlSource

# ========== Imports from current package ==========
from pipelineBatcher.ui import app as BatcherUI


QML_DIR = Path(__file__).parent.parent / "ui" / "qml"


# 
# Register QML folder
# 

registerQmlSource(
    folder=QML_DIR,
    name="PipelineBatcher",
    major=1,
    minor=0,
)


# 
# Callback to open the UI
# 

class OpenPipelineBatcher(MenuCallback):
    _app = None
    _backend = None
    _window = None
    
    @classmethod
    def _onWindowDestroyed(cls):
        cls._window = None

    @classmethod
    def getBackend(cls, app):
        if cls._backend is None:
            cls._backend = BatcherUI.PipelineBatcherBackend(parent=app)
        return cls._backend
    
    @classmethod
    def initApp(cls, app, engine):
        if cls._app is None:
            backend = cls.getBackend(app)
            app._pipelineBatcherBackend = backend
            engine.rootContext().setContextProperty(
                "pipelineBatcherBackend", backend
            )
            logging.info("Backend registered as context property.")

    @classmethod
    def open(cls, app):
        engine = app.engine
        cls.initApp(app, engine)
        cls._backend.reset()
        cls._backend.pageChanged.emit(0)

        if cls._window is None:
            window_url = QUrl.fromLocalFile(os.path.join(QML_DIR, "app.qml"))
            component = QQmlComponent(engine, window_url)
            if component.status() != QQmlComponent.Status.Ready:
                logging.error(f"Failed to load QML window: {component.errorString()}")
                return
            cls._window = component.create(engine.rootContext())
            if cls._window is None:
                logging.error("QML window creation returned None.")
                return
            QObject.setParent(cls._window, engine)
            cls._window.destroyed.connect(cls._onWindowDestroyed)

        cls._window.show()

    def __call__(self, menu, app, **kwargs):
        try:
            self.open(app)
        except Exception as exc:
            logging.exception(f"Error opening window: {exc}")


# 
# Create the menu
# 

batcher_menu = Menu("Batcher", tooltip="Meshroom production tools")

batcher_menu.addButton(
    "batcher",
    label="Pipeline Batcher UI",
    callback=OpenPipelineBatcher(),
    tooltip="Open the TemplateBatcher UI.",
    shortcut="Ctrl+Shift+B",
)

register_menu(batcher_menu)
