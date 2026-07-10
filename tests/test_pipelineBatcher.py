import os
from pathlib import Path
from pipelineBatcher.ui import utilities
# from pipelineBatcher.ui import entityProvider as EntityHelper
import meshroom.core


TEST_RESOURCES = Path(__file__).parent / "resources"


class TestTemplateHelper:

    @classmethod
    def setup_class(cls):
        cls.__old_env = os.environ
        os.environ["PIPELINE_RESOURCES"] = str(TEST_RESOURCES)
        meshroom.core.initNodes()
        meshroom.core.initPipelines()

    @classmethod
    def teardown_class(cls):
        os.environ = cls.__old_env

    # def test_get_templates_dir(self):
    #     tpl_dir = TplHelper.get_templates_dir()
    #     assert Path(tpl_dir).exists()
    #     assert Path(tpl_dir).stem == "batchPipelines"
    
    # def test_list_templates(self, tplFolder):
    #     tpls = TplHelper.list_templates(tplFolder)
    #     assert isinstance(tpls, list)
    #     for tpl in tpls:
    #         assert isinstance(tpl, dict)
    #         template = tpl["template"]
    #         assert Path(template).exists()
    #         assert Path(template).suffix == ".mg"
    #         entity_type = tpl["input_entity_type"]
    #         assert entity_type in (
    #             "Asset", "Shot", "Sequence", "Version" 
    #         )
    #         input_entity_params = tpl["input_entity_params"]
    #         assert isinstance(input_entity_params, dict)
    #         assert len(input_entity_params) >= 1
    
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
