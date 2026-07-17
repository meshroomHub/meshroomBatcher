name = "meshroomBatcher"

release_version = "0.1.1"

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
    # LINT
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
    },
    # TEST
    "pytest": {
        "command": (
            "python -m pytest "
            "--cov=pipelineBatcher "
            "--cov-config={root}/.coveragerc "
            "--cov-report=xml:coverage.xml "
            "--cov-report=html:htmlcov "
            "--cov-report=term "
            "-v "
            "{root}/tests/"
        ),
        "requires": ["python-3.11", "pytest-8.2", "pytestCov"],
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
    env.MESHROOM_BATCHER_RESOURCES.append("{this.root}/resources")
    # Providers
    env.MESHROOM_BATCHER_PROVIDERS.append("{this.root}/python/providers")
    # Menu
    env.MESHROOM_PLUGINS_PATH.append("{this.root}/python/pipelineBatcher")
    # Alias
    alias("meshroomBatcher", "python {this.root}/python/pipelineBatcher/ui")
    alias("meshroomBatcherDev", "MESHROOM_INSTANT_CODING=1 python {this.root}/python/pipelineBatcher/ui")
