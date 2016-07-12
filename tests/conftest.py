#
import pytest
import subprocess

def pytest_report_header(config):
    freeze = subprocess.check_output(['pip', 'freeze'])
    return "QuakeML test runner: qmlutil" + '\n' + freeze

def pytest_addoption(parser):
    parser.addoption("--integration", action="store_true", 
        help="run integration tests")
    parser.addoption("--writefiles", action="store_true", 
        help="Write test files for inspection")

