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

