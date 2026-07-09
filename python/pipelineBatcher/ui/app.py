"""
Python Backend of the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import json
import logging
import functools
import traceback
from enum import Enum

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
                logging.error(f"{fn.__name__} error: {exc}\n{traceback.format_exc()}")
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
        self._state = utilities.TemplateCreationState()
    
    def reset(self):
        self._busyMessage = ""
        self._page  = PipelineBatcherPages.PAGE_TEMPLATE
        self._state = utilities.TemplateCreationState()

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

    @busy_slot("Instanciate pipeline")
    def _launch(self):
        try:
            utilities.instantiate_pipelines(self._state)
        except Exception as exc:  # noqa: BLE001
            self.errorOccurred.emit(str(exc))

    # --- Async slots : use busy_slot to make sure the UI displays the busy overlay ---

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
        self._state.entity_type = tpl.get("input_entity_type", "") if tpl else ""
        self.templateSelected.emit(self._state.entity_type)
        self.next()

    @busy_slot("Fetching entities")
    @Slot(str, result=str)
    def getEntitiesTree(self, entity_type: str) -> str:
        """Return a JSON array representing the navigation tree.

        Each item on the dict has the following keys:
        - id: unique identifier used to fetch entities
        - label: display name
        - icon: (optional) icon to show before the label
        - children: leaf nodes (eg. for Asset -> each asset type)
        """
        logging.info(f"Get entities tree for entity type: {entity_type}")
        try:
            tree = EntitiesHelper.get_entities_tree(entity_type)
            return json.dumps(tree, ensure_ascii=False)
        except Exception as exc:
            logging.error(f"getEntitiesTree error: {exc}\n{traceback.format_exc()}")
            self.errorOccurred.emit(str(exc))
            return json.dumps([])

    # Not a busy slot because it's quick
    @Slot(str, str, result=str)
    def fetchEntitiesByGroup(self, entity_type: str, group_id: str) -> str:
        """Return a JSON array of entity dicts that belong to a group ID within entity_type.
        
        Each item on the dict has the following keys:
        - id: unique entity id (passed to setSelectedEntities)
        - name: display name
        - status: (optional) status of the item, displayed as a coloured badge
        - description: (optional) description shown in the third column
        """
        try:
            entities = EntitiesHelper.fetch_entities_by_group(entity_type, group_id)
            return json.dumps(entities, ensure_ascii=False)
        except Exception as exc:
            logging.error(f"fetchEntitiesByGroup error: {exc}\n{traceback.format_exc()}")
            self.errorOccurred.emit(str(exc))
            return json.dumps([])

    @busy_slot("Set selected entities")
    @Slot(str)
    def setSelectedEntities(self, entities_json: str):
        """Receive the entity ids checked on EntityPage."""
        self._state.selected_entities = json.loads(entities_json)
        self.next()

    @busy_slot("Fetching parameter info")
    @Slot(str, str, result=str)
    def getParamInfo(self, mg_path: str, node_param: str) -> str:
        """Return JSON dict with type/default/choices for a 'NodeInstance:paramName'.
        """
        try:
            node_instance, param_name = utilities.parseNodeParam(node_param)
            info = TemplatesHelper.getMgParameterInfo(mg_path, node_instance, param_name)
            return json.dumps(info, ensure_ascii=False)
        except Exception as exc:
            logging.warning(f"getParamInfo error: {exc}")
            return json.dumps({"type": "string", "default": "", "choices": []})

    @busy_slot("Set parameters")
    @Slot(str)
    def setParameters(self, params_json: str):
        """Receive the parameter values filled on ParameterPage."""
        self._state.parameters = json.loads(params_json)
        self.next()

    @busy_slot("Set parameters")
    def instantiate_pipelines(self):
        import time
        time.sleep(2)
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

    # --- Qt Signals and Properties ---

    busyChanged = Signal(bool)
    busyMessageChanged = Signal(str)
    pageChanged = Signal(int)
    templateSelected = Signal(str)   # emits input_entity_type after template selection
    errorOccurred = Signal(str)
    page = Property(int, lambda self: self._page.value, constant=True)
    entityType = Property(str, lambda self: self._state.entity_type, constant=True)
    busy = Property(bool, _get_busy, _set_busy, notify=busyChanged)
    busyMessage = Property(str, _get_busy_message, notify=busyChanged)
