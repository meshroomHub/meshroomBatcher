import tempfile
import pytest
from pathlib import Path


TEST_RESOURCES = Path(__file__).parent / "resources"


@pytest.fixture
def tempFolder():
    with tempfile.TemporaryDirectory() as tmpFolder:
        yield tmpFolder

@pytest.fixture
def tplFolder():
    path = TEST_RESOURCES / "batchPipelines"
    return str(path)

@pytest.fixture
def createSceneTemplateJson():
    path = TEST_RESOURCES / "batchPipelines" / "create_scene.json"
    return str(path)

@pytest.fixture
def createSceneTemplateMg():
    path = TEST_RESOURCES / "batchPipelines" / "create_scene.mg"
    return str(path)
