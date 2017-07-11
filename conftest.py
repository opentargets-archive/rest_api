import pytest
def pytest_addoption(parser):
    parser.addoption("--es", action="store_true",
        help="run tests that require ES")