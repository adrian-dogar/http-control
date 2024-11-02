import unittest
from unittest.mock import patch, mock_open, MagicMock
from app.collection import Collection, load_config, configure_collection, setup_logging

class TestCollection(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data="key=value\nanother_key=another_value")
    def test_load_config(self, mock_file):
        config = load_config('config.yaml')
        self.assertIsInstance(config, dict)

    @patch('builtins.open', new_callable=mock_open, read_data="key=value\nanother_key=another_value")
    def test_configure_collection_with_env(self, mock_file):
        collection = configure_collection('config.yaml', 'env.file', verbose=True)
        self.assertIsInstance(collection, Collection)

    @patch('builtins.open', new_callable=mock_open, read_data="key=value\nanother_key=another_value")
    def test_configure_collection_without_env(self, mock_file):
        collection = configure_collection('config.yaml', verbose=True)
        self.assertIsInstance(collection, Collection)

    @patch('builtins.open', new_callable=mock_open, read_data="key=value\nanother_key=another_value")
    def test_setup_logging_to_file(self, mock_file):
        logger = setup_logging('logfile.log')
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.FileHandler)

    @patch('builtins.open', new_callable=mock_open, read_data="key=value\nanother_key=another_value")
    def test_setup_logging_to_stdout(self, mock_file):
        logger = setup_logging()
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)

    def test_collection_append(self):
        collection = Collection()
        request = MagicMock()
        collection.append(request)
        self.assertEqual(len(collection.requests), 1)

    def test_collection_get_items(self):
        collection = Collection()
        request = MagicMock()
        collection.append(request)
        items = collection.get_items()
        self.assertEqual(len(items), 1)

    def test_collection_build_report(self):
        collection = Collection()
        request = MagicMock()
        request.assertions = [{'status': True}, {'status': False}]
        collection.append(request)
        with patch('app.collection.logger') as mock_logger:
            collection.build_report()
            self.assertTrue(mock_logger.info.called)

if __name__ == '__main__':
    unittest.main()