import requests
import json
from urllib.parse import urlparse, parse_qs, urlencode
import urllib3
import globals
from logger import setup_logger
logger = setup_logger(__name__)

# TODO: should I leave it here?????
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Request:
    def __init__(self, attributes, variables=None):
        logger.debug("Initializing Request")


        self.id = None
        self.name = ''
        self.summary = ''
        self.suite = None
        self.tags = []
        self.groups = []
        self.url = ''
        self.method = ''
        self.data = None  # TODO if dict, dump to json
        self.json = None  # TODO if dict, dump to json
        self.headers = {}
        self.verify = {}
        self.cert = []
        self.proxies = {}
        self.expected = {}
        self.response = {}
        self.timeout = 10
        self.assertions = []

        for key, value in attributes.items():
            if key not in ['url', 'payload', 'keystore', 'truststore', 'proxies']:
                setattr(self, key, value)

        self.method = attributes.get('method', 'GET')
        self.headers = attributes.get('headers', {})
        self.url = self.replace_variables(attributes['url'], variables)
        self.verify = attributes.get('truststore', False)
        self.cert = attributes.get('keystore', [])
        self.proxies = attributes.get('proxy', None)

        # Either "json" or "data" can be used, but not both
        if 'payload' in attributes and attributes['payload']:
            try:
                self.json = json.loads(attributes['payload'])
            except (TypeError, ValueError):
                logger.debug("Payload is not a JSON")
        else:
            self.data = attributes.get('payload', None)

    def invoke(self):
        logger.info(f"Sending {self.method} request to {self.url}")
        try:
            response = requests.request(
                method=self.method,
                url=self.url,
                json=self.json if self.json else None,
                data=self.data if self.data else None,
                headers=self.headers,
                verify=self.verify,
                cert=tuple(self.cert),
                proxies=self.proxies
            )
            # response.raise_for_status()
            logger.info(f"Request successful. Status code: {response.status_code}")

            try:
                response_body = response.json()
            except ValueError:
                response_body = response.text

            outcome = {
                "body": response_body,
                "headers": response.headers,
                "status_code": response.status_code,
                "error": ""
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            outcome = {
                "body": "",
                "headers": {},
                "status_code": "",
                "error": str(e)
            }

        self.response = outcome

    def replace_variables(self, url, variables):
        if not variables:
            return url

        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        for key, value in query_params.items():
            if value[0].startswith('$'):
                var_name = value[0][1:]
                if var_name in variables:
                    query_params[key] = [variables[var_name]]

        new_query = urlencode(query_params, doseq=True)
        return parsed_url._replace(query=new_query).geturl()

