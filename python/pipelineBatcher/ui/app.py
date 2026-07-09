"""
Python Backend of the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import json
import logging
import functools
from enum import Enum
from typing import Any
from dataclasses import dataclass, field

# ========== External libraries ==========
from PySide6.QtCore import (
    QCoreApplication, 
    QObject, 
    QEventLoop, 
    QTimer, 
    Slot, 
    Signal, 
    Property
)

# ========== Imports from current package ==========
from pipelineBatcher.ui import utilities
from pipelineBatcher.ui import templates as TemplatesHelper
from pipelineBatcher.ui import entities as EntitiesHelper


class PipelineBatcherPages(Enum):
    PAGE_TEMPLATE  = 0
    PAGE_ENTITY    = 1
    PAGE_PARAMETER = 2


@dataclass
class TemplateCreationState:
    selected_template: dict | None = None
    selected_entities: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)

    def reset(self):
        self.selected_template = None
        self.selected_entities.clear()
        self.parameters.clear()

    @property
    def needs_parameter_page(self) -> bool:
        return bool(
            self.selected_template
            and self.selected_template.get("parameters")
        )


def busy_slot(message: str = ""):
    """
    Decorator that shows the busy overlay for one frame before executing
    the blocking slot.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            self._busyMessage = message
            self.busyMessageChanged.emit(message)
            self._set_busy(True)
            # Let the UI render one frame
            loop = QEventLoop()
            QTimer.singleShot(50, loop.quit)
            loop.exec()
            # Now run the blocking work
            try:
                return fn(self, *args, **kwargs)
            except Exception as exc:
                logging.error(f"{fn.__name__} error: {exc}")
                self.errorOccurred.emit(str(exc))
            finally:
                self._busyMessage = ""
                self.busyMessageChanged.emit(message)
                self._set_busy(False)
        return wrapper
    return decorator


class PipelineBatcherBackend(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._templates_dir = TemplatesHelper.get_templates_dir()
        self._templatesIndex = TemplatesHelper.buildTemplatesIndex(self._templates_dir)
        self._app   = parent
        self._busy  = False
        self._busyMessage = ""
        self._page  = PipelineBatcherPages.PAGE_TEMPLATE
        self._state = TemplateCreationState()

    def _get_busy(self) -> bool:
        return self._busy

    def _set_busy(self, value: bool):
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit(value)
            self.forceUpdate()
                
    def _get_busy_message(self) -> str:
        return self._busyMessage

    @staticmethod
    def forceUpdate():
        QCoreApplication.processEvents()

    # --- Navigation ---
    
    @Slot(result=bool)
    def hasParametersPage(self):
        return self._state.needs_parameter_page

    @Slot()
    def next(self):
        nextIndex = self._page.value + 1
        if nextIndex not in map(lambda x: x.value, PipelineBatcherPages):
            # Last page -> launch
            self._launch()
            return
        nextPage = PipelineBatcherPages(nextIndex)
        if nextPage == PipelineBatcherPages.PAGE_PARAMETER and not self.hasParametersPage():
            self._launch()
        else:
            self._go_to(nextPage)

    @Slot()
    def back(self):
        previousIndex = self._page.value - 1
        if previousIndex in map(lambda x: x.value, PipelineBatcherPages):
            self._go_to(PipelineBatcherPages(previousIndex))

    @Slot()
    def cancel(self):
        self._state.reset()
        self._go_to(PipelineBatcherPages.PAGE_TEMPLATE)
        # TODO : exit instead

    def _go_to(self, page: PipelineBatcherPages):
        if self._page != page:
            self._page = page
            self.pageChanged.emit(page.value)

    def _launch(self):
        try:
            self.instantiate_pipelines()
        except Exception as exc:  # noqa: BLE001
            self.errorOccurred.emit(str(exc))

    def instantiate_pipelines(self):
        state = self._state
        template = state.selected_template
        print(f"[instantiate_pipelines] template {template}")
        print(f"[instantiate_pipelines] state {state}")
        # for param_key, param_value in state.parameters.items():
        #     node, attr = param_key.split(":")
        #     graph.node(node).attribute(attr).value = param_value
        for i, entity in enumerate(state.selected_entities):
            # node, param = template["input_entity_param"].split(":")
            # graph.node(node).attribute(param).value = entity
            print(f"[instantiate_pipelines] {i}/{len(state.selected_entities)} - entity {entity}")

    # --- Exchange infos ---

    @busy_slot("Fetching templates")
    @Slot(result=str)
    def listTemplates(self) -> str:
        """Return JSON array of template descriptors."""
        templates = [self._templatesIndex[i] for i in sorted(self._templatesIndex.keys())]
        return json.dumps(templates, ensure_ascii=False)

    @busy_slot("Select the chosen template")
    @Slot(int)
    def selectTemplate(self, index):
        """Receive the template chosen on TemplatePage and advance."""
        logging.info(f"Selected template {index}")
        self._state.reset()
        tpl = self._templatesIndex.get(index)
        self._state.selected_template = tpl
        # Notify QML so EntityPage can set its entityType before the page transition
        entity_type = tpl.get("input_entity_type", "") if tpl else ""
        self.templateSelected.emit(entity_type)
        self.next()

    @Slot(str)
    def setSelectedEntities(self, entities_json: str):
        """Receive the entity ids checked on EntityPage (no auto-advance)."""
        self._state.selected_entities = json.loads(entities_json)
        self.next()

    @Slot(str)
    def setParameters(self, params_json: str):
        """Receive the parameter values filled on ParameterPage (no auto-advance)."""
        self._state.parameters = json.loads(params_json)

    # --- Qt Signals and Properties ---

    busyChanged = Signal(bool)
    busyMessageChanged = Signal(str)
    pageChanged = Signal(int)
    templateSelected = Signal(str)   # emits input_entity_type after template selection
    errorOccurred = Signal(str)
    busy = Property(bool, _get_busy, _set_busy, notify=busyChanged)
    busyMessage = Property(str, _get_busy_message, notify=busyChanged)
