import os
import yaml
from address_formatter import Address

path = os.path.join('address-formatter-templates', 'testcases', 'countries')
test_files = sorted(filter(os.path.isfile, [os.path.join(path, file) for file in os.listdir(path)]))
for test_file in test_files:
    print('---------------------------')
    print(test_file)
    print('---------------------------')
    print("")
    with open(test_file, 'r') as ymlfile:
        test_cases = yaml.safe_load_all(ymlfile)
        for test_case in test_cases:
            print('Components: ' + str(test_case['components']))
            print('')
            address = Address(**test_case['components'])
            print(address.format())
