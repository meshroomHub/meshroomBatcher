"""
Python Backend of the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import json

# ========== External libraries ==========
from PySide6.QtCore import QObject, Slot, Signal, Property

# ========== Meshroom imports ==========
from meshroom.common import Property
# ========== Imports from current package ==========
from pipelineBatcher.ui import templates as TemplatesHelper


class PipelineBatcherBackend(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._templates_dir = TemplatesHelper.get_templates_dir()
        self._app = parent
        self._busy = False

    @property
    def busy(self):
        return self._busy
    
    @busy.setter
    def busy(self, value: bool):
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit(value)

    @Slot(result=str)
    def listTemplates(self) -> str:
        """ Return JSON array of template descriptors. """
        templates = TemplatesHelper.list_templates(self._templates_dir)
        return json.dumps(templates, ensure_ascii=False)

    busyChanged = Signal(bool)
    busy = Property(bool, busy, notify=busyChanged)
    errorOccurred = Signal(str)
