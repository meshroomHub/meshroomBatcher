{
    "header": {
        "releaseVersion": "2026.1.0+develop",
        "fileVersion": "2.1",
        "nodesVersions": {
            "GetScene": "1.0",
            "GetShotInfo": "1.0",
            "InputString": "1.0"
        },
        "template": true
    },
    "graph": {
        "GenerateNukeScene_1": {
            "nodeType": "GetScene",
            "position": [
                209,
                227
            ],
            "inputs": {
                "shotName": "{GetShotInfo_1.shot}",
                "task": "env",
                "vup": true,
                "dcc": "nuke",
                "fromTemplate": true,
                "template": "{TEMPLATE_1.output}"
            },
            "internalInputs": {
                "color": ""
            }
        },
        "GetShotInfo_1": {
            "nodeType": "GetShotInfo",
            "position": [
                -35,
                145
            ],
            "inputs": {
                "shot": "{ShotCode_1.string}"
            }
        },
        "ShotCode_1": {
            "nodeType": "InputString",
            "position": [
                -238,
                234
            ],
            "inputs": {}
        },
        "TEMPLATE_1": {
            "nodeType": "GetScene",
            "position": [
                -34,
                333
            ],
            "inputs": {
                "type": "Asset",
                "assetType": "util",
                "assetName": "templates",
                "task": "env",
                "dcc": "nuke"
            },
            "internalInputs": {
                "color": ""
            }
        }
    }
}