import json

from request import Request
import itertools
from logger import setup_logger

class Collection:
    requests = []
    tags = []
    groups = []
    suites = []

    def __init__(self, data=None):
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing Collection")

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
            self.requests.append(request)

    def get_atomized_collection(self, tags=None, groups=None, suites=None):
        atomized_collection = []
        for request in self.requests:
            if self._is_request_included(request):
                atomized_collection.append(request)
        return atomized_collection

    def parse_requests_in(self, object):
        """
        Read, interpret and return the requests list
        :return:
        """
        self.logger.info("Loading requests list...")
        collection = []
        defaults = object.get('defaults', {})
        requests_list = object.get('requests', [])

        for item in requests_list:
            attributes = {
                'method': item['invoke'].get('method', defaults.get('method', 'GET')),
                'truststore': item['invoke'].get('truststore', defaults.get('truststore')),
                'keystore': item['invoke'].get('keystore', defaults.get('keystore', [])),
                'proxy': item['invoke'].get('proxy', defaults.get('proxy', {})),
                'headers': item['invoke'].get('headers', defaults.get('headers', {})),
                'payload': item['invoke'].get('payload', defaults.get('payload', None)),
            }

            if 'url' in item['invoke']:
                attributes['url'] = item['invoke']['url']

            elif 'url_values' in item['invoke'] and 'url_template' in defaults['request']:
                # Use itertools to iterate ove the url_values and build all options
                processed_dict = {k: [v] if isinstance(v, str) else v for k, v in item['invoke']['url_values'].items()}
                keys = processed_dict.keys()
                value_lists = processed_dict.values()
                combinations = list(itertools.product(*value_lists))
                result = [dict(zip(keys, combo)) for combo in combinations]
                self.logger.debug(f"result is {result}")

                for option in result:
                    self.logger.debug(f"one options is : {option}")
                    attributes['url'] = defaults['requests']['url_template'].format(**option)
                    del attributes['url_values']
                    self.logger.debug(f"attributes are {attributes}")
                    request = Request(attributes)
                    self.append(request)

                self.logger.debug(f"collection's requests are {len(self.requests)}")
            elif 'url' in defaults:
                attributes['url'] = defaults['url']
            else:
                self.logger.error("No URL provided for request")
                return []

            request = Request(attributes)
            self.append(request)


