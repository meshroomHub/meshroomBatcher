"""
Python Backend of the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ========== External libraries ==========
from PySide6.QtCore import QObject, Slot, Signal

# ========== Meshroom imports ==========
from meshroom.common import Property

# ========== Imports from current package ==========
from pipelineBatcher.ui import templates as TemplatesHelper


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


class PipelineBatcherBackend(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._templates_dir = TemplatesHelper.get_templates_dir()
        self._templatesIndex = TemplatesHelper.buildTemplatesIndex(self._templates_dir)
        self._app   = parent
        self._busy  = False
        self._page  = PipelineBatcherPages.PAGE_TEMPLATE
        self._state = TemplateCreationState()

    def _get_busy(self) -> bool:
        return self._busy

    def _set_busy(self, value: bool):
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit(value)
    
    # --- Navigation ---

    @Slot()
    def next(self):
        nextIndex = self._page.value + 1
        if nextIndex not in map(lambda x: x.value, PipelineBatcherPages):
            # Last page -> launch
            self._launch()
            return
        nextPage = PipelineBatcherPages(nextIndex)
        if nextPage == PipelineBatcherPages.PAGE_PARAMETER and not self._state.needs_parameter_page:
            self._launch()
        else:
            self._go_to(nextPage)

    @Slot()
    def back(self):
        previousIndex = self._page.value - 1
        if previousIndex in map(lambda x: x.value, PipelineBatcherPages):
            self._go_to(self.PipelineBatcherPages(previousIndex))

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
        self._set_busy(True)
        try:
            self.instantiate_pipelines()
        except Exception as exc:  # noqa: BLE001
            self.errorOccurred.emit(str(exc))
        finally:
            self._set_busy(False)

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

    @Slot(result=str)
    def listTemplates(self) -> str:
        """Return JSON array of template descriptors."""
        templates = [self._templatesIndex[i] for i in sorted(self._templatesIndex.keys())]
        return json.dumps(templates, ensure_ascii=False)

    @Slot(int)
    def selectTemplate(self, index):
        """Receive the template chosen on TemplatePage and advance."""
        logging.info(f"Selected template {index}")
        self._state.reset()
        tpl = self._templatesIndex.get(index)
        self._state.selected_template = tpl
        self.next()

    @Slot(str)
    def setSelectedEntities(self, entities_json: str):
        """Receive the entity ids checked on EntityPage (no auto-advance)."""
        self._state.selected_entities = json.loads(entities_json)

    @Slot(str)
    def setParameters(self, params_json: str):
        """Receive the parameter values filled on ParameterPage (no auto-advance)."""
        self._state.parameters = json.loads(params_json)

    # --- Qt Signals and Properties ---

    busyChanged    = Signal(bool)
    busy = Property(bool, _get_busy, _set_busy, notify=busyChanged)
    pageChanged    = Signal(int)
    errorOccurred  = Signal(str)
