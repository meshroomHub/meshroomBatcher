"""
Helpers for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========

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
