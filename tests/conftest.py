import json
import os
import pytest


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true",
        help="include slow tests")

def pytest_runtest_setup(item):
    for opt in ['slow']:
        if opt in item.keywords and not item.config.getoption("--%s" % opt):
            pytest.skip("need --%s option to run" % opt)

@pytest.fixture
def example_fixture():
    return "example fixture. Obviously this should be some sort of complicated class " \
           "that is either expensive to construct or often used..."


def resources_path(package):
    dir_path = os.path.join(os.path.dirname(__file__), package)
    return os.path.join(dir_path, 'resources')


def resource(package, filename):
    return os.path.join(resources_path(package), filename)


def resource_as_text(package, filename):
    path = resource(package, filename)
    with open(path, 'r', encoding='utf-8') as infile:
        return infile.read()


def resource_as_json(package, filename):
    return json.loads(resource_as_text(package, filename))


# Paths to resources e.g.,
# FOO = resource('package/', 'bar.txt')  ; for 'tests/package/resources/bar.txt'
#...


# pytest fixtures e.g.,
#@pytest.fixture
#def foo():
#    return FOO
