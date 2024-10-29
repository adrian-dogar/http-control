import json
import argparse
from configobj import Config
from agent import Agent
from collection import Collection
from logger import setup_logger
from request import Request

def main():
    logger = setup_logger(__name__)

    # Read arguments
    parser = argparse.ArgumentParser(description="Run the application")
    parser.add_argument("collection", nargs='?', help="Configuration file")
    args = parser.parse_args()

    # Load configuration files
    collection_file = Config(args.collection).items()
    logger.debug(f"Configuration file loaded: {args.collection}")
    # logger.debug(f"Configuration: {json.dumps(collection_file, indent=2)}")

    # Run the control operator
    logger.info("Setting up the agent")
    agent = Agent()

    collection = Collection(collection_file)
    logger.debug(f"Collection length: {len(collection.requests)}")

    if len(collection.requests) == 0:
        logger.error("No requests found")
        return

    logger.warning(f"Collection: {collection.requests}")

    for counter, (index, request) in enumerate(collection.requests.items()):
        request.invoke()
        logger.debug(f"Response message: {request.response['body']}")

        if request.response['body']:
            agent.evaluate_response(request)


if __name__ == "__main__":
    main()