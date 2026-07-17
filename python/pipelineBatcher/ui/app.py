"""
Python Backend of the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import os
import sys
import time
import subprocess
import json
import logging
import functools
import traceback
from enum import Enum
from pathlib import Path

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

# ========== Imports from meshroom ==========
from meshroom import _MESHROOM_ROOT

# ========== Imports from current package ==========
from pipelineBatcher.utilities import parseNodeParam, getMgParameterInfo, import_provider
from pipelineBatcher.entityProvider import EntityProviderRegistry, TemplateInfo
from pipelineBatcher.ui.instanciation import TemplateCreationState, TemplateInstanciator


class PipelineBatcherPages(Enum):
    PAGE_TEMPLATE  = 0
    PAGE_ENTITY    = 1
    PAGE_PARAMETER = 2
    PAGE_FINAL     = 3


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
        # Register providers
        providersRoot = Path(__file__).parent.parent.parent / "providers"
        for provider in providersRoot.iterdir():
            if not provider.name.endswith("Provider.py"):
                continue
            try:
                import_provider(str(provider))
            except Exception as e:
                logging.error(f"Failed to register provider from file {provider}: {e}.\n\n{traceback.format_exc()}")
        self._templatesIndex: dict[int, TemplateInfo] = EntityProviderRegistry.getTemplateIndex()
        self._app   = parent
        self.reset()

    def reset(self):
        self._busy  = False
        self._busyMessage = ""
        self._page  = PipelineBatcherPages.PAGE_TEMPLATE
        self._state = TemplateCreationState()
        self._instanciator = None

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
        if nextIndex == PipelineBatcherPages.PAGE_FINAL.value+1:
            self.reset()
            self.closeRequested.emit()
            return
        if nextIndex not in map(lambda x: x.value, PipelineBatcherPages):
            logging.warning(f"Cannot go to page {nextIndex} : unknown page")
            return
        nextPage = PipelineBatcherPages(nextIndex)
        if nextPage == PipelineBatcherPages.PAGE_PARAMETER and not self.hasParametersPage():
            # Skip parameter page, jump straight to PAGE_FINAL
            self._go_to(nextPage)
            self.next()
        elif nextPage == PipelineBatcherPages.PAGE_FINAL:
            self._prepareInstanciator()
            self._go_to(nextPage)
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
        if self._page == PipelineBatcherPages.PAGE_TEMPLATE:
            self.reset()
            self.closeRequested.emit()
        else:
            self._go_to(PipelineBatcherPages.PAGE_TEMPLATE)

    def _go_to(self, page: PipelineBatcherPages):
        if self._page != page:
            self._page = page
            self.pageChanged.emit(page.value)

    @busy_slot("Build pipeline instanciator")
    def _prepareInstanciator(self):
        try:
            self._instanciator = TemplateInstanciator(self._app, self._state)
            self.instanciatorChanged.emit()
        except Exception as exc:
            logging.error(f"Failed to prepare instanciator: {exc}\n{traceback.format_exc()}")
            self.errorOccurred.emit(str(exc))

    def getSelectedTemplatePath(self):
        return self._state.selected_template.template

    def getSelectedTemplateParams(self):
        return self._state.selected_template.parameters

    # --- Async slots : use busy_slot to make sure the UI displays the busy overlay ---

    @busy_slot("Fetching templates")
    @Slot(result=str)
    def listTemplates(self) -> str:
        """Return JSON array of template descriptors."""
        templates = [self._templatesIndex[i].toDict() for i in sorted(self._templatesIndex.keys())]
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
        self._state.entity_type = tpl.input_entity_type if tpl else ""
        self.templateSelected.emit(self._state.entity_type)
        self.next()

    @busy_slot("Fetching entities")
    @Slot(result=str)
    def getEntitiesTree(self) -> str:
        """Return a JSON array representing the navigation tree.

        Each item on the dict has the following keys:
        - id: unique identifier used to fetch entities
        - label: display name
        - icon: (optional) icon to show before the label
        - children: leaf nodes (eg. for Asset -> each asset type)
        """
        try:
            templateIndex = self._state.selected_template.index
            templateName = EntityProviderRegistry.getTemplateName(templateIndex)
            logging.info(f"Get entities tree for template index: {templateName}")
            tree = EntityProviderRegistry.getEntityTree(templateIndex)
            return json.dumps(tree, ensure_ascii=False)
        except Exception as exc:
            logging.error(f"getEntitiesTree error: {exc}\n{traceback.format_exc()}")
            self.errorOccurred.emit(str(exc))
            return json.dumps([])

    # Not a busy slot because it's quick
    @Slot(str, result=str)
    def fetchEntitiesByGroup(self, group_id: str) -> str:
        """Return a JSON array of entity dicts that belong to a group ID within entity_type.
        
        Each item on the dict has the following keys:
        - id: unique entity id (passed to setSelectedEntities)
        - name: display name
        - status: (optional) status of the item, displayed as a coloured badge
        - description: (optional) description shown in the third column
        """
        try:
            templateIndex = self._state.selected_template.index
            entities = EntityProviderRegistry.fetchEntitiesByGroup(templateIndex, group_id)
            serializedEntities = [e.toDict() for e in entities]
            return json.dumps(serializedEntities, ensure_ascii=False)
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
    @Slot(str, result=str)
    def getParamInfo(self, node_param: str) -> str:
        """Return JSON dict with type/default/choices for a 'NodeInstance:paramName'.
        """
        mg_path = self.getSelectedTemplatePath()
        try:
            node_instance, param_name = parseNodeParam(node_param)
            info = getMgParameterInfo(mg_path, node_instance, param_name)
            return json.dumps(info, ensure_ascii=False)
        except Exception as exc:
            logging.warning(f"getParamInfo error: {exc}")
            return json.dumps({"type": "unknown", "default": "", "choices": []})

    @Slot(str)
    def setParameters(self, params_json: str):
        """Receive the parameter values filled on ParameterPage."""
        self._state.parameters = json.loads(params_json)

    @busy_slot("Opening scene...")
    @Slot(str)
    def openMeshroomScene(self, path: str):
        """Receive the parameter values filled on ParameterPage."""
        meshroomRoot = Path(_MESHROOM_ROOT)
        meshroomUI = meshroomRoot / "meshroom" / "ui"
        if not meshroomUI.exists():
            logging.error(f"Could not find Meshroom UI module: {meshroomUI}")
            return

        # Build the environment variables based on the OS
        env = os.environ.copy()
        if sys.platform == "win32":
            env["MESHROOM_INSTALL_DIR"] = str(meshroomRoot)

        # Build the command
        command = [sys.executable, str(meshroomUI), path]
        try:
            levelName = logging.getLevelName(logging.getLogger().level)
            if levelName:
                command.extend(["-v", levelName.lower()])
        except Exception:
            pass

        logging.info(f"Open Meshroom scene: {command}")
        try:
            subprocess.Popen(command, env=env)
        except Exception as e:
            logging.error(f"Failed to open Meshroom scene: {e}")
        else:
            # Wait for some time while the window open
            time.sleep(3)

    # --- Qt Signals and Properties ---
    pageChanged = Signal(int)
    page = Property(int, lambda self: self._page.value, constant=True)
    errorOccurred = Signal(str)
    closeRequested = Signal()
    busyChanged = Signal(bool)
    busy = Property(bool, _get_busy, _set_busy, notify=busyChanged)
    busyMessageChanged = Signal(str)
    busyMessage = Property(str, _get_busy_message, notify=busyChanged)
    templateSelected = Signal(str)   # emits input_entity_type after template selection
    entityType = Property(str, lambda self: self._state.entity_type, constant=True)
    templateParameters = Property('QVariantList', getSelectedTemplateParams, constant=True)
    instanciatorChanged = Signal()
    instanciator = Property(QObject, lambda self: self._instanciator, notify=instanciatorChanged)
