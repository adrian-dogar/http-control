import pytest
import json
import logging
from http_agent import make_request

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_config(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)


def compare_response(response, expected):
    assert response.status_code == expected[
        'status_code'], f"Expected status code {expected['status_code']}, got {response.status_code}"

    if 'headers' in expected:
        for key, value in expected['headers'].items():
            assert key in response.headers, f"Expected header {key} not found in response"
            assert response.headers[key] == value, f"Expected header {key} to be {value}, got {response.headers[key]}"

    if 'body_contains' in expected:
        response_json = response.json()
        for key in expected['body_contains']:
            assert key in response_json, f"Expected key {key} not found in response body"

    assert response.ok != expected[
        'error'], f"Error status mismatch. Expected error: {expected['error']}, got: {not response.ok}"


def pytest_addoption(parser):
    parser.addoption("--variables", action="store", default="{}", help="JSON string of variables")


@pytest.fixture
def variables(request):
    return json.loads(request.equests_config.getoption("--variables"))


@pytest.fixture
def config():
    return load_config('../input_data/test_requests.json')


def handle_config_variables(config, variables):
    updated_requests = []
    for req in config['requests']:
        updated_req = req.copy()
        for key, value in req.items():
            if isinstance(value, str):
                for var, val in variables.items():
                    updated_req[key] = updated_req[key].replace(f'${var}', str(val))
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, str):
                        for var, val in variables.items():
                            updated_req[key][subkey] = updated_req[key][subkey].replace(f'${var}', str(val))
        updated_requests.append(updated_req)
    return updated_requests


@pytest.mark.parametrize("request_config", load_config('../input_data/test_requests.json')['requests'])
def test_http_requests(request_config, variables):
    logger.info(f"Testing request: {request_config['name']}")

    # Apply variables to the request configuration
    updated_request_config = handle_config_variables({"requests": [request_config]}, variables)[0]

    response = make_request(updated_request_config)
    assert response is not None, "Request failed"
    compare_response(response, updated_request_config['expected_response'])
    logger.info(f"Test passed for request: {updated_request_config['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])