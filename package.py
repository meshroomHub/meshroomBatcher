name = "meshroomBatcher"

release_version = "1.0.0"

@early()
def version():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "release":
        return release_version
    return "develop"


plugin_for=["meshroom"]

requires = [
    "python-3.9+<3.12",
]

private_build_requires = ["cmake-3"]

tests = {
    "pylint": {
        "command": "pylint {root}/python/{name} --rcfile={root}/pyproject.toml",
        "requires": ["pylint-2.17"],
    },
    "ruff": {
        "command": "ruff check {root}/python/{name} --config={root}/pyproject.toml",
        "requires": ["ruff-0.14"],
    },
    "black_diff": {
        "command": "black {root}/python --diff --check --config={root}/pyproject.toml",
        "requires": ["black-23.9"],
    },
    "black": {
        "command": "black {root}/python --config={root}/pyproject.toml",
        "requires": ["black-23.9"],
        "run_on": "explicit",
    }
}

with scope("config") as config:
    # Specify the path where the package will be install with the command rez release
    config.release_packages_path = "/s/apps/packages/mikrosVfx/multiview"
    config.plugins = {
        "release_vcs": {
            "tag_name": release_version
        }
    }

def commands():
    env.PYTHONPATH.append("{this.root}/python")
    # Production Pipelines
    env.MESHROOM_PIPELINE_TEMPLATES_PATH.append("{this.root}/resources/pipelines")

    # Menu
    env.MESHROOM_PLUGINS_PATH.append("{this.root}/python/pipelineBatcher")
