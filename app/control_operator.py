# from configobj.config import Config
import re

import requests

import http_agent as agent
import json
import yaml
import logging
import sys
import traceback


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_requests():
    logger.info("Loading requests list")
    try:
        with open('../input_data/test_requests.yaml', 'r', encoding='utf-8') as f:
            requests = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading requests: {str(e)}")
        return

    return requests

def prepare(custom, defaults=None):
    logger.info(f"Preparing request [{custom['name'] if 'name' in custom else 'unnamed'}]")

    request = {
        'method': custom.get('method', defaults.get('method', 'GET')),
        'truststore': custom.get('truststore', defaults.get('truststore')),
        'keystore': custom.get('keystore', defaults.get('keystore', False)),
        'proxy': custom.get('proxy', defaults.get('proxy', None)),
        'headers': custom.get('headers', defaults.get('headers', {})),
        'payload': custom.get('payload', defaults.get('payload', None)),
    }

    if 'url' in custom:
        request['url'] = custom['url']
    elif 'url_values' in custom and 'url_template' in defaults:
        request['url'] = defaults['url_template'].format(**custom['url_values'])
    elif 'url' in defaults:
        request['url'] = defaults['url']
    else:
        logger.error("No URL provided for request")
        return

    return request

# Example usage:
# def test_function():
#     x = 5
#     y = 10
#
#     assert_and_go(x < y, "x should be smaller than y")
#     assert_and_go(x > y, "x should be greater than y")
#     assert_and_go(isinstance(x, str), "x should be a string")
#
#     print("This will be executed even if assertions fail")
#
#
# test_function()

def prepare_response(response):
    logger.debug(f"Preparing response")
    if type(response) == requests.Response:
        result = {
            'status_code': response.status_code,
            'headers': response.headers,
        }

        if response.headers['Content-Type'] == 'application/json':
            result['body'] = response.json()
        elif response.headers['Content-Type'] == 'application/xml':
            result['body'] = response.text
        else:
            result['body'] = response.text

        return result

def assert_and_go(condition, message=None):
    logger.debug(f"Asserting: {message}")
    try:
        assert condition, message

    except AssertionError as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = traceback.extract_tb(exc_traceback)
        filename, line, func, text = tb[-1]

        details = f"Assertion failed on line {line} in {filename}:\n"
        details += f"    {text}\n"
        if message:
            details += f"Message: {message}\n"

        logger.error(f"Assertion failed: {message}")
        return {
            "status": False,
            "message": f"Assertion failed: {message}",
            "details": details
        }

        # You can choose to re-raise the exception, return False, or handle it in any other way
        # For example, to continue execution:

    logger.info(f"Assertion passed: {message}")
    return {
        "status": True,
        "message": f"Assertion passed: {message}",
        "details": ""
    }

def prepare_and_assert(prop, test, expected_value, current_value):
    logger.debug(f"Preparing and asserting {prop}, for {test} test, with expected value {expected_value} and current value {current_value}")
    if test == 'contains':
        result = assert_and_go(
            condition=expected_value in current_value,
            message=f"Expected {prop} to contain {expected_value}, but it doesn't"
        )
        return result

    elif test == 'equals':
        if type(expected_value) == dict:
            norm_expected = re.sub(r'[\n\r\t\s]+', '', json.dumps(expected_value, sort_keys=True))
            norm_current = re.sub(r'[\n\r\t\s]+', '', json.loads(json.dumps(current_value, sort_keys=True)))
            condition = norm_expected == norm_current
            message = f"Expected {prop} to be {norm_expected}, got {norm_current}"
        else:
            condition = expected_value == current_value
            message = f"Expected {prop} to be {expected_value}, got {current_value}"
        result = assert_and_go(
            condition=condition,
            message=message
        )
        return result

    elif test == 'greater':
        result = assert_and_go(
            condition=current_value > expected_value,
            message=f"Expected {prop} to be greater than {expected_value}, got {current_value}"
        )
        return result
    elif test == 'lower':
        result = assert_and_go(
            condition=current_value < expected_value,
            message=f"Expected {prop} to be lower than {expected_value}, got {current_value}"
        )
        return result
    elif test == 'exists':
        result = assert_and_go(
            condition=current_value is not None,
            message=f"Expected {prop} to exist, but it doesn't"
        )
        return result
    elif test == 'not_exists':
        result = assert_and_go(
            condition=current_value is None,
            message=f"Expected {prop} to not exist, but it does"
        )
        return result
    elif test == 'type':
        result = assert_and_go(
            condition=type(current_value) == expected_value,
            message=f"Expected {prop} to be of type {expected_value}, got {type(current_value)}"
        )
        return result
    elif test == 'length':
        result = assert_and_go(
            condition=len(current_value) == expected_value,
            message=f"Expected {prop} to have length {expected_value}, got {len(current_value)}"
        )
        return result
    elif test == 'empty':
        result = assert_and_go(
            condition=len(current_value) == 0,
            message=f"Expected {prop} to be empty, but it isn't"
        )
        return result
    elif test == 'not_empty':
        result = assert_and_go(
            condition=len(current_value) > 0,
            message=f"Expected {prop} to not be empty, but it is"
        )
        return result
    elif test == "in_range":
        window = sorted(expected_value.split(":"))

        result = assert_and_go(
            condition=int(window[0]) <= int(current_value) <= int(window[1]),
            message=f"Expected {prop} to be in range {expected_value}, got {current_value}"
        )
        return result
    else:
        return False, f"Unknown test type: {test}"


def evaluate_response(response, expected):
    logger.info("Evaluating response")
    for prop in expected.keys():
        logger.info(f"Evaluating response property {prop}")
        for test in expected[prop]:
            logger.info(f"Evaluating response property test {test}")
            # print(f"test: {test}")
            # print(list(test.keys())[0])
            # print(test[list(test.keys())[0]])
            # if isinstance(test[list(test.keys())[0]], dict):
            #     check = list(test.keys())[0]
            #     # check = test[list(test.keys())[0]]
            # else:
            #     check = list(test.keys())[0]
            check = list(test.keys())[0]
            # print(check)
            message = prepare_and_assert(prop, check, test[check], response[prop])

def main():
    # config_parser = Config("config.json", env_file=".env")
    # config = config_parser.items()

    requests_list = read_requests()

    if len(requests_list['comms']) == 0:
        logger.error("No requests found")
        return

    for item in requests_list['comms']:
        new_request = prepare(item['request'], requests_list['defaults']['request'])
        logger.debug(json.dumps(new_request))

        response = agent.make_request(new_request)
        logger.debug(json.dumps(response.json()))

        if response:
            response = prepare_response(response)
            evaluate_response(response, item['expected_response'])

if __name__ == "__main__":
    main()