import unittest
import json
from unittest.mock import patch, mock_open
from config_manager import ConfigManager, ConfigurationError

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        # Mock configuration data
        self.config_data = {
            'strategies': {
                'strategy1': {
                    'param1': 'value1',
                    'param2': 'value2'
                },
                'strategy2': {
                    'param1': 'value3',
                    'param2': 'value4'
                }
            }
        }
        self.config_json = json.dumps(self.config_data)
        
    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_load_config_file_not_found(self, mock_file):
        mock_file.side_effect = FileNotFoundError
        with self.assertRaises(ConfigurationError):
            ConfigManager('fake_path')

    @patch('builtins.open', new_callable=mock_open, read_data='not_a_json')
    def test_load_config_invalid_json(self, mock_file):
        with self.assertRaises(ConfigurationError):
            ConfigManager('fake_path')

    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_missing_strategies_key(self, mock_file):
        with self.assertRaises(ConfigurationError):
            config_manager = ConfigManager('fake_path')
            config_manager.validate_config()

    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_save_config_io_error(self, mock_file):
        mock_file.side_effect = IOError("cannot write to file")
        config_manager = ConfigManager('fake_path')
        with self.assertRaises(ConfigurationError):
            config_manager.save_config()

    @patch('builtins.open', new_callable=mock_open, read_data=config_json)
    def test_get_strategy_config(self, mock_file):
        config_manager = ConfigManager('fake_path')
        strat_config = config_manager.get_strategy_config('strategy1')
        self.assertEqual(strat_config, self.config_data['strategies']['strategy1'])

    @patch('builtins.open', new_callable=mock_open, read_data=config_json)
    def test_update_config_valid(self, mock_file):
        config_manager = ConfigManager('fake_path')
        new_data = {'strategies': {'strategy3': {'param1': 'value5'}}}
        config_manager.update_config(new_data)
        self.assertIn('strategy3', config_manager.current_config['strategies'])

# Run the tests
if __name__ == '__main__':
    unittest.main()
