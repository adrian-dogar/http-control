import re
import json
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
        expected = request.expected
        response = request.response
        result = []
        for propiedad in expected.keys():
            for test in expected[propiedad]:
                logger.debug(f"Evaluating <{propiedad}> response property on <{test}> condition")
                check = list(test.keys()).pop(0)
                result.append(self.prepare_and_assert(propiedad, check, test[check], response[propiedad]))
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
            f"Preparing and asserting <{prop}>, for <{test}> test, with expected value <{expected_value}> and current value <{current_value}>")

        if test == 'contains':
            if type(expected_value) == dict:
                condition = all(item in current_value.items() for item in expected_value.items())
            elif type(expected_value) == list:
                condition = all(item in current_value for item in expected_value)
            else:
                condition = expected_value in current_value

            result = self.assert_and_go(
                condition=condition,
                message=f"Expected <{prop}> to contain <{expected_value}>, got <{current_value}>"
            )
            return result

        elif test == 'includes':
            try:
                if type(expected_value) == dict:
                    condition = all(item in current_value.items() for item in expected_value.items())
                    message = f"Expected <{prop}> to include <{expected_value}>, got <{current_value}>"
                else:
                    condition = expected_value in current_value
                    message = f"Expected <{prop}> to include <{expected_value}>, got <{current_value}>"
            except AttributeError or TypeError:
                condition = False
                message = f"Expected <{prop}> to include <{expected_value}>, got <{current_value}>"

            result = self.assert_and_go(
                condition=condition,
                message=message
            )
            return result

        elif test == 'equals':
            if type(expected_value) == dict:
                norm_expected = re.sub(r'[\n\r\t\s]+', '', json.dumps(expected_value, sort_keys=True))
                norm_current = re.sub(r'[\n\r\t\s]+', '', json.dumps(current_value, sort_keys=True))
                condition = norm_expected == norm_current
                message = f"Expected <{prop}> to be {norm_expected}, got {norm_current}"
            else:
                condition = expected_value == current_value
                message = f"Expected <{prop}> to be <{expected_value}>, got <{current_value}>"
            result = self.assert_and_go(
                condition=condition,
                message=message
            )
            return result

        elif test == 'greater':
            result = self.assert_and_go(
                condition=current_value > expected_value,
                message=f"Expected <{prop}> to be greater than <{expected_value}>, got <{current_value}>"
            )
            return result

        elif test == 'lower':
            result = self.assert_and_go(
                condition=current_value < expected_value,
                message=f"Expected <{prop}> to be lower than <{expected_value}>, got <{current_value}>"
            )
            return result

        elif test == 'exists':
            result = self.assert_and_go(
                condition=current_value is not None,
                message=f"Expected <{prop}> to exist, got <{current_value}>"
            )
            return result

        elif test == 'not_exists':
            result = self.assert_and_go(
                condition=current_value is None,
                message=f"Expected <{prop}> to not exist, got <{current_value}>"
            )
            return result

        elif test == 'type':
            result = self.assert_and_go(
                condition=type(current_value) == expected_value,
                message=f"Expected <{prop}> to be of type <{expected_value}>, got {type(current_value)}"
            )
            return result

        elif test == 'length':
            result = self.assert_and_go(
                condition=len(current_value) == expected_value,
                message=f"Expected <{prop}> to have length <{expected_value}>, got {len(current_value)}"
            )
            return result

        elif test == 'empty':
            result = self.assert_and_go(
                condition=len(current_value) == 0,
                message=f"Expected <{prop}> to be empty, got <{current_value}>"
            )
            return result

        elif test == 'not_empty':
            result = self.assert_and_go(
                condition=len(current_value) > 0,
                message=f"Expected <{prop}> to not be empty, got <{current_value}>"
            )
            return result

        elif test == "in_range":
            window = sorted(expected_value.split(":"))

            try:
                condition = int(window[0]) <= int(current_value) <= int(window[1])
            except ValueError:
                condition = False

            result = self.assert_and_go(
                condition=condition,
                message=f"Expected <{prop}> to be in range <{expected_value}>, got <{current_value}>"
            )
            return result

        elif test == "matches":
            result = self.assert_and_go(
                condition=re.fullmatch(expected_value, str(current_value)),
                message=f"Expected <{prop}> to match <{expected_value}>, got <{current_value}>"
            )
            return result

        else:
            return False, f"Unknown test type: {test}"