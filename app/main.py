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
    collection_file = Config(args.collection, ".env").items()
    logger.debug(f"Configuration file loaded: {args.collection}")

    oauth2_providers = collection_file.get('defaults').get('oauth2')
    for provider, provider_details in oauth2_providers.items():
        if provider_details.get('enabled'):
            logger.debug(f"Fetching token from provider: {provider}")
            ltm = LightTokenManager(
                provider_details['token_url'],
                provider_details['client_id'],
                provider_details['client_secret'],
                provider_details['scope'],
                provider_details['grant_type'],
            )
            # create new entry in globals, using the provider name as key
            globals.tokens[provider] = ltm.get_token()
            print(f"token: {globals.tokens}")

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
        logger.info(f"New request!\n    Processing {index}/{len(collection.requests)} - {request.name}")
        request.invoke()
        logger.debug(f"Response message: {request.response['body']}")

        result = agent.evaluate_response(request)
        request.assertions = result

    logger.info("All requests have been processed")

    collection.build_report()

# TODO: make it run as script but also as a module
if __name__ == "__main__":
    main()