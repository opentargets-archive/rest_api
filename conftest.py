import pytest
def pytest_addoption(parser):
    parser.addoption("--es", action="store_true", default=False, help="run tests that require ES")