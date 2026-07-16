import os
from pathlib import Path
from pipelineBatcher import utilities
import meshroom.core


TEST_RESOURCES = Path(__file__).parent / "resources"


class TestTemplateHelper:

    @classmethod
    def setup_class(cls):
        cls.__old_env = os.environ
        meshroom.core.initNodes()
        meshroom.core.initPipelines()

    @classmethod
    def teardown_class(cls):
        os.environ = cls.__old_env

    def test_getMgParameterInfo(self, createSceneTemplateMg):
        params = {
            ("ShotCode_1", "string"): "string",
            ("InputString_1", "string"): "string",
            ("InputInt_1", "integer"): "int",
        }
        for nodeInstance, paramName in params.keys():
            paraminfo = utilities.getMgParameterInfo(createSceneTemplateMg, nodeInstance, paramName)
            assert set(paraminfo.keys()) == {"type", "default", "choices", "node", "paramName"}
            expectedType = params[(nodeInstance, paramName)]
            assert paraminfo["type"] == expectedType
