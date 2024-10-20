import requests
import logging
import json
from urllib.parse import urlparse, parse_qs, urlencode

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def make_request(request_config, variables=None):
    url = replace_variables(request_config['url'], variables)
    method = request_config['method']
    payload = request_config.get('payload')
    headers = request_config.get('headers', {})

    logger.info(f"Making {method} request to {url}")

    try:
        response = requests.request(
            method=method,
            url=url,
            json=payload,
            headers=headers,
            verify=request_config.get('truststore'),
            cert=request_config.get('keystore'),
            proxies=request_config.get('proxy')
        )
        response.raise_for_status()
        logger.info(f"Request successful. Status code: {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return None


def replace_variables(url, variables):
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
