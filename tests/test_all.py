import os
import yaml
from address_formatter import format


def test_all():
    path = os.path.join('address-formatting', 'testcases', 'countries')
    test_files = sorted(filter(os.path.isfile, [os.path.join(path, file) for file in os.listdir(path)]))
    for test_file in test_files:

        with open(test_file, 'r') as ymlfile:
            test_cases = yaml.safe_load_all(ymlfile)
            for test_case in test_cases:
                # Attempt to undo YAML parser logic that converts ON (e.g. as in Ontario) to True
                for k, v in test_case['components'].items():
                    if isinstance(v, bool):
                        test_case['components'][k] = 'ON' if v else 'OFF'

                address = format(**test_case['components'])
                assert address == test_case['expected']
