import json
import itertools
import random
import string
from request import Request
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
        self.id_counter = 0
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

    def parse_requests_in(self, object):
        """
        Read, interpret and return the requests list
        :return:
        """
        logger.info("Loading requests list...")
        defaults = object.get('defaults', {})
        requests_list = object.get('requests', [])

        for item in requests_list:
            logger.info(f"Gathering attributes for request [{item.get('name')}] - ({self.id_counter})")
            attributes = {
                'method': item['invoke'].get('method', defaults.get('method', 'GET')),
                'truststore': item['invoke'].get('truststore', defaults.get('truststore')),
                'keystore': item['invoke'].get('keystore', defaults.get('keystore', [])),
                'proxy': item['invoke'].get('proxy', defaults.get('proxy', {})),
                'headers': item['invoke'].get('headers', defaults.get('headers', {})),
                'payload': item['invoke'].get('payload', defaults.get('payload', None)),
                'name': item.get('name', ''),
                'summary': item.get('summary', ''),
                'tags': item.get('tags', []),
                'groups': item.get('groups', []),
                'suite': slugify(item.get('name', rand(7))),
                'expected' : item.get('expected', {})
            }

            if 'url' in item['invoke']:
                attributes['url'] = item['invoke']['url']
                request = Request(attributes)
                self.append(request)

            elif 'url' in defaults:
                attributes['url'] = defaults['url']
                request = Request(attributes)
                self.append(request)

            elif 'url_values' in item['invoke'] and 'url_template' in defaults['request']:
                # Use itertools to iterate over the url_values and build all options
                processed_dict = {k: [v] if isinstance(v, str) else v for k, v in item['invoke']['url_values'].items()}
                keys = processed_dict.keys()
                value_lists = processed_dict.values()
                combinations = list(itertools.product(*value_lists))
                all_options = [dict(zip(keys, combo)) for combo in combinations]
                logger.debug(f"All options are: {all_options}")

                for option in all_options:
                    logger.info(f"Creating new request for the [{attributes['suite']}] suite - ({self.id_counter})")
                    attributes['url'] = defaults['request']['url_template'].format(**option)
                    logger.debug(f"Attributes for current option are: {attributes}")
                    request = Request(attributes)
                    self.append(request)

            else:
                logger.error("No URL provided for request")
                return []

    def add_response(self, index, response):
        self.requests[index].response = response


