import itertools
import random
import string
from request import Request
from urllib.parse import urlparse

from logger import setup_logger
logger = setup_logger(__name__)

def rand(length=7):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def slugify(text):
    return text.lower().replace(' ', '-')

# Singleton class
class Collection:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Collection, cls).__new__(cls)
        return cls._instance

    def __init__(self, data=None):
        logger.info("Initializing Collection")
        self.id_counter = 1
        self.requests = {}
        self.tags = []
        self.groups = []
        self.suites = []

        if data:
            self.parse_requests_in(data)

    def get_items(self):
        return self.requests

    def append(self, request: Request, tags=None, groups=None, suite=None):
        if suite:
            request.suite = suite
            self.suites.append(suite)
        if tags:
            request.tags = tags
            self.tags.extend(tags)
        if groups:
            request.groups = groups
            self.groups.extend(groups)

        # Use the id_counter as the unique key
        request.id = self.id_counter
        self.requests[self.id_counter] = request
        self.id_counter += 1  # Increment the counter

    def get_atomized_collection(self, tags=None, groups=None, suites=None):
        """
        TODO underdeveloped
        Return a list of requests that match the tags, groups and suites
        :param tags:
        :param groups:
        :param suites:
        :return:
        """
        atomized_collection = []
        for request in self.requests.values():
            if self._is_request_included(request):
                atomized_collection.append(request)
        return atomized_collection

    def parse_requests_in(self, data):
        """
        Read, interpret and return the requests list
        :return:
        """
        logger.info("Loading requests list...")
        defaults = data.get('defaults', {}).get('request', {})
        requests_list = data.get('requests', [])

        for item in requests_list:
            logger.info(f"Instantiating the requests for [{item.get('name')}] suite - ({self.id_counter})")
            invoke = item.get('invoke', {})
            attributes = {
                'method': invoke.get('method', defaults.get('method', 'GET')),
                'truststore': invoke.get('truststore', defaults.get('truststore')),
                'keystore': invoke.get('keystore', defaults.get('keystore', [])),
                'headers': {**defaults.get('headers', {}), **invoke.get('headers', {})},
                'payload': invoke.get('payload', defaults.get('payload', None)),
                'name': item.get('name', ''),
                'summary': item.get('summary', ''),
                'tags': item.get('tags', []),
                'groups': item.get('groups', []),
                'suite': slugify(item.get('name', rand(7))),
                'expected' : item.get('expect', {}),
                'timeout': item.get('timeout', defaults.get('timeout', 10)),
            }

            if 'url' in invoke:
                attributes['url'] = invoke['url']
                request = Request(attributes)
                self.append(request)

            elif 'url' in defaults:
                attributes['url'] = defaults['url']
                request = Request(attributes)
                self.append(request)

            elif 'url_values' in invoke and 'url_template' in defaults:
                processed_dict = {k: [v] if isinstance(v, str) else v for k, v in invoke['url_values'].items()}
                keys = processed_dict.keys()
                value_lists = processed_dict.values()
                combinations = list(itertools.product(*value_lists))
                all_options = [dict(zip(keys, combo)) for combo in combinations]
                logger.debug(f"All options are: {all_options}")

                for option in all_options:
                    logger.debug(f"Creating new request for the <{attributes['suite']}> suite - ({self.id_counter})")
                    attributes['url'] = defaults['url_template'].format(**option)
                    logger.debug(f"Attributes for current option are: {attributes}")
                    request = Request(attributes)
                    self.append(request)

            else:
                logger.error("No URL provided for request")
                return []

            hostname = urlparse(attributes['url']).hostname
            attributes['bypass_proxy'] = False
            for substring in data.get('defaults', {}).get('bypass_proxy', {}):
                if f"{substring}" in hostname:
                    attributes['bypass_proxy'] = True
                    break
            if attributes['bypass_proxy']:
                attributes['proxy'] = invoke.get('proxy', defaults.get('proxy', {}))

    def build_report(self):
        logger.info("Building report...")

        total_requests = len(self.requests)
        logger.info(f"    > Total requests: {total_requests}")

        total_assertions = sum([len(request.expected) for request in self.requests.values()])
        logger.info(f"    > Total assertions: {total_assertions}")

        total_failed_assertions = sum(len([assertion for assertion in request.assertions if assertion['status'] == False]) for request in self.requests.values())
        logger.info(f"    > Total failed assertions: {total_failed_assertions}")

        total_passed_assertions = sum(len([assertion for assertion in request.assertions if assertion['status'] == True]) for request in self.requests.values())
        logger.info(f"    > Total passed assertions: {total_passed_assertions}")

        requests_for_review = {request.id: request.name for request in self.requests.values() if len([assertion for assertion in request.assertions if assertion['status'] == False]) > 0}
        logger.info(f"    > Requests with failed assertions:")
        for request_id, value in requests_for_review.items():
            logger.info(f"        >> ({request_id}): {value}")

        logger.info("Report built successfully!")