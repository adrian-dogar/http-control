import requests
import json
from urllib.parse import urlparse, parse_qs, urlencode
from logger import setup_logger

class Request:
    suite = None
    tags = []
    groups = []
    url = ''
    method = ''
    data = None
    json = None
    headers = {}
    verify = {}
    cert = []
    proxies = {}

    def __init__(self, attributes, variables=None):
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing Request")
        self.logger.info(f"Initializing {attributes}")

        self.url = self.replace_variables(attributes['url'], variables)
        self.method = attributes.get('method', 'GET')
        self.headers = attributes.get('headers', {})

        if 'payload' in attributes and attributes['payload']:
            try:
                self.json = json.loads(attributes['payload'])
            except (TypeError, ValueError):
                self.logger.debug("Payload is not a JSON")
        else:
            self.data = attributes.get('payload', None)

    def invoke(self):
        self.logger.info(f"Sending {self.method} request to {self.url}")
        try:
            response = requests.request(
                method=self.method,
                url=self.url,
                json=self.payload,
                headers=self.headers,
                verify=self.verify,
                cert=self.cert,
                proxies=self.proxies
            )
            response.raise_for_status()
            self.logger.info(f"Request successful. Status code: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            return None

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
