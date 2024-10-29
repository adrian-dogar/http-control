import re
import requests
import json
import yaml
import sys
import traceback

from logger import setup_logger
logger = setup_logger(__name__)

# Singleton class
class Agent():
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Agent, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    def evaluate_response(self, request):
        logger.info("Evaluating response")
        expected = request.expected
        response = request.response
        result = []
        for propiedad in expected.keys():
            logger.info(f"Evaluating response property {propiedad}")
            for test in expected[propiedad]:
                logger.info(f"Evaluating response property test {test}")
                check = list(test.keys()).pop(0)
                result.append(self.prepare_and_assert(propiedad, check, test[check], response[propiedad]))

    def prepare_request(self, custom, defaults=None):
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

    def prepare_response(self, response):
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

    def assert_and_go(self, condition, message=None):
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

        logger.info(f"Assertion passed: {message}")
        return {
            "status": True,
            "message": f"Assertion passed: {message}",
            "details": ""
        }

    def prepare_and_assert(self, prop, test, expected_value, current_value):
        logger.debug(
            f"Preparing and asserting {prop}, for {test} test, with expected value {expected_value} and current value {current_value}")

        if test == 'contains':
            result = self.assert_and_go(
                condition=expected_value in current_value,
                message=f"Expected {prop} to contain {expected_value}, but it doesn't"
            )
            return result

        elif test == 'includes':
            if type(expected_value) == dict:
                condition = all(item in current_value.items() for item in expected_value.items())
                message = f"Expected {prop} to include {expected_value}, but it doesn't"
            else:
                condition = expected_value in current_value
                message = f"Expected {prop} to include {expected_value}, but it doesn't"
            result = self.assert_and_go(
                condition=condition,
                message=message
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
            result = self.assert_and_go(
                condition=condition,
                message=message
            )
            return result

        elif test == 'greater':
            result = self.assert_and_go(
                condition=current_value > expected_value,
                message=f"Expected {prop} to be greater than {expected_value}, got {current_value}"
            )
            return result

        elif test == 'lower':
            result = self.assert_and_go(
                condition=current_value < expected_value,
                message=f"Expected {prop} to be lower than {expected_value}, got {current_value}"
            )
            return result

        elif test == 'exists':
            result = self.assert_and_go(
                condition=current_value is not None,
                message=f"Expected {prop} to exist, but it doesn't"
            )
            return result

        elif test == 'not_exists':
            result = self.assert_and_go(
                condition=current_value is None,
                message=f"Expected {prop} to not exist, but it does"
            )
            return result

        elif test == 'type':
            result = self.assert_and_go(
                condition=type(current_value) == expected_value,
                message=f"Expected {prop} to be of type {expected_value}, got {type(current_value)}"
            )
            return result

        elif test == 'length':
            result = self.assert_and_go(
                condition=len(current_value) == expected_value,
                message=f"Expected {prop} to have length {expected_value}, got {len(current_value)}"
            )
            return result

        elif test == 'empty':
            result = self.assert_and_go(
                condition=len(current_value) == 0,
                message=f"Expected {prop} to be empty, but it isn't"
            )
            return result

        elif test == 'not_empty':
            result = self.assert_and_go(
                condition=len(current_value) > 0,
                message=f"Expected {prop} to not be empty, but it is"
            )
            return result

        elif test == "in_range":
            window = sorted(expected_value.split(":"))

            result = self.assert_and_go(
                condition=int(window[0]) <= int(current_value) <= int(window[1]),
                message=f"Expected {prop} to be in range {expected_value}, got {current_value}"
            )
            return result

        elif test == "matches":
            result = self.assert_and_go(
                condition=re.fullmatch(expected_value, current_value),
                message=f"Expected {prop} to match {expected_value}, got {current_value}"
            )
            return result

        else:
            return False, f"Unknown test type: {test}"