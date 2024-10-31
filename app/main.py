import argparse
from configobj import Config
from agent import Agent
from collection import Collection
from logger import setup_logger
from light_token_manager import LightTokenManager
import globals

def main():
    logger = setup_logger(__name__)

    # Read arguments
    parser = argparse.ArgumentParser(description="Run the application")
    parser.add_argument("collection", nargs='?', help="Configuration file")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase output verbosity")
    args = parser.parse_args()

    globals.verbose = args.verbose

    # Load configuration files
    collection_file = Config(args.collection).items()
    logger.debug(f"Configuration file loaded: {args.collection}")
    # logger.debug(f"Configuration: {json.dumps(collection_file, indent=2)}")

    # TODO: must be improved.
    provider = collection_file.get('defaults').get('oauth2').get('my_provider')
    ltm = LightTokenManager(provider['token_url'], provider['client_id'], provider['client_secret'], provider['scope'], provider['grant_type'])
    globals.token = ltm.get_token()

    # Run the control operator
    logger.info("Setting up the agent")
    agent = Agent()

    collection = Collection(collection_file)
    logger.debug(f"Collection length: {len(collection.requests)}")

    if len(collection.requests) == 0:
        logger.error("No requests found")
        return

    logger.debug(f"Collection: {collection.requests}")

    for counter, (index, request) in enumerate(collection.requests.items()):
        request.invoke()
        logger.debug(f"Response message: {request.response['body']}")

        result = agent.evaluate_response(request)
        request.assertions = result

    logger.info("All requests have been processed")

    collection.build_report()

if __name__ == "__main__":
    main()