"""
Standalone PipelineBatcherUI
"""

# ========== Py standard lib imports ==========
import sys
import os
import signal
import logging
import argparse
from pathlib import Path

# ========== External libraries ==========
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtQml import QQmlApplicationEngine

try:
    from PySide6 import shiboken6
except ImportError:
    import shiboken6

# ========== Meshroom imports ==========
import meshroom
from meshroom.common import strtobool
from meshroom.ui.utils import QFileSystemWatcher

# ========== Imports from current package ==========
from pipelineBatcher.ui.utilities import import_provider
from pipelineBatcher.ui.app import PipelineBatcherBackend


meshroom.core.initNodes()


# Disable QML disk cache so hot reload always picks up source changes
os.environ["QML_DISABLE_DISK_CACHE"] = "1"

QML_DIR = Path(__file__).parent.parent / "ui" / "qml"
MESHROOM_QML_DIR = Path(meshroom.__file__).parent / "ui" / "qml"
HOT_RELOAD_DEBOUNCE_MS = 500


def parse_args():
    parser = argparse.ArgumentParser(description="Pipeline Batcher UI")
    parser.add_argument(
        "--mock", action="store_true", help="Add the mock Entity Provider.",
    )
    parser.add_argument(
        "-v", "--verbosity",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Set the logging level (default: info)",
    )

    args = parser.parse_args()

    # Set logging stream handler
    for handler in logging.getLogger().handlers:
        logging.getLogger().removeHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s.%(msecs)03d][%(name)s][%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    ))
    logging.getLogger().setLevel(getattr(logging, args.verbosity.upper()))
    logging.getLogger().addHandler(handler)

    return args


def add_mock_provider():
    path = Path(__file__).parent.parent.parent / "mock" / "mockEntityProvider.py"
    import_provider(str(path))


class PipelineBatcherApp:

    def __init__(self, backend: PipelineBatcherBackend):
        self._backend = backend
        self._window = None
        self._engine = None

        self._watcher = QFileSystemWatcher()
        if strtobool(os.getenv("MESHROOM_INSTANT_CODING", "0")):
            for qml_file in QML_DIR.rglob("*.qml"):
                self._watcher.addPath(str(qml_file))
            self._watcher.fileChanged.connect(self._on_file_changed)
            logging.info("Watching %d QML files under %s", len(self._watcher.files()), QML_DIR)

        self._debounce = QTimer(singleShot=True, interval=HOT_RELOAD_DEBOUNCE_MS)
        self._debounce.timeout.connect(self.load)

        self.load()

    def _make_engine(self) -> QQmlApplicationEngine:
        engine = QQmlApplicationEngine()
        engine.setOutputWarningsToStandardError(True)

        # Register QML import paths
        if MESHROOM_QML_DIR.is_dir():
            engine.addImportPath(str(MESHROOM_QML_DIR))
        engine.addImportPath(QML_DIR)
        engine.rootContext().setContextProperty("pipelineBatcherBackend", self._backend)
        return engine

    def load(self):
        logging.debug("Loading QML window")

        # Save geometry before destroying the old window
        old_pos = None
        old_size = None
        if self._window is not None and shiboken6.isValid(self._window):
            old_pos = self._window.position()
            old_size = self._window.size()
            self._window.closing.disconnect(self._on_window_closing)
            self._window.close()
            shiboken6.delete(self._window)
            self._window = None

        # Trim and destroy the old engine so compiled components are released
        if self._engine is not None and shiboken6.isValid(self._engine):
            self._engine.trimComponentCache()
            shiboken6.delete(self._engine)
            self._engine = None

        self._engine = self._make_engine()

        def on_object_created(obj, url):
            if obj is None:
                logging.error("Failed to create QML window.")
                return
            self._window = obj
            self._window.closing.connect(self._on_window_closing)
            if old_pos is not None:
                obj.setPosition(old_pos)
            if old_size is not None:
                obj.resize(old_size)
            obj.show()
        
        self._engine.objectCreated.connect(on_object_created)
        self._engine.load(QUrl.fromLocalFile(str(QML_DIR / "app.qml")))
        self._engine.objectCreated.disconnect(on_object_created)

    def _on_file_changed(self, filepath):
        if not strtobool(os.getenv("MESHROOM_INSTANT_CODING", "0")):
            return
        logging.debug("File changed: %s", filepath)
        self._watcher.addPath(filepath)  # Re-add in case of atomic save (e.g. vim, PyCharm)
        self._debounce.start()

    def _on_window_closing(self):
        logging.debug("User closed the window, quitting.")
        QApplication.quit()


args = parse_args()

if args.mock:
    add_mock_provider()

# Allow Ctrl+C to kill the app from the terminal
signal.signal(signal.SIGINT, signal.SIG_DFL)

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
backend = PipelineBatcherBackend(parent=app)
ui = PipelineBatcherApp(backend)
app.exec()
