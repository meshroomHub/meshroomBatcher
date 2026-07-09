"""
Helpers for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
from typing import Any
from dataclasses import dataclass, field

# ========== External libraries ==========

# ========== Meshroom imports ==========

# ========== Imports from current package ==========


def parseNodeParam(nodeParam: str):
    """ Split "NodeInstance:paramName" into ("NodeInstance", "paramName").
    """
    parts = nodeParam.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Expected 'NodeInstance:paramName', got '{nodeParam}'")
    return (parts[0].strip(), parts[1].strip())


@dataclass
class TemplateCreationState:
    entity_type: str = ""
    selected_template: dict | None = None
    selected_entities: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)

    def reset(self):
        self.entity_type = ""
        self.selected_template = None
        self.selected_entities.clear()
        self.parameters.clear()

    @property
    def needs_parameter_page(self) -> bool:
        return bool(
            self.selected_template
            and self.selected_template.get("parameters")
        )


def instantiate_pipelines(state):
    import time
    time.sleep(2)
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

