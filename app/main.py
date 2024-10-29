import json
import argparse
from configobj import Config
from agent import Agent
from app.collection import Collection
from request import Request

from logger import setup_logger

def main():
    logger = setup_logger(__name__)

    # Read arguments
    parser = argparse.ArgumentParser(description="Run the application")
    parser.add_argument("collection", nargs='?', help="Configuration file")
    args = parser.parse_args()

    # Load configuration files
    collection_file = Config(args.collection).items()
    logger.debug(f"Configuration file loaded: {args.collection}")
    logger.debug(f"Configuration: {json.dumps(collection_file, indent=2)}")

    # Run the control operator
    logger.info("Running the control operator")
    agent = Agent()

    collection = Collection(collection_file)
    logger.debug(f"Collection length: {len(collection.requests)}")

    if len(collection.requests) == 0:
        logger.error("No requests found")
        return

    for request in collection.requests:
        response = request.invoke()
        logger.debug(json.dumps(response.json()))

        if response:
            response = agent.prepare_response(response)
            agent.evaluate_response(response, request['expected_response'])


if __name__ == "__main__":
    main()