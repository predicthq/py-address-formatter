import os
from os import path
from namedlist import namedtuple
import yaml

Config = namedtuple('Config', ['components', 'component_aliases', 'templates', 'state_codes', 'county_codes', 'country_lang'])


def load_config(template_path):
    templates = {}
    components = {}
    component_aliases = {}
    state_codes = {}
    county_codes = {}
    country_lang = {}

    if not path.isdir(template_path):
        raise IOError('Address formatting templates path cannot be found.')

    # Parse components and component aliases
    with open(path.join(template_path, 'components.yaml'), 'r') as ymlfile:
        comps = yaml.safe_load_all(ymlfile)

        for comp in comps:
            if 'aliases' in comp:
                component_aliases.update({alias: comp['name'] for alias in comp['aliases']})

            components[comp['name']] = comp.get('aliases')

    # Parse templates
    with open(path.join(template_path, 'countries', 'worldwide.yaml'), 'r') as ymlfile:
        templates = yaml.safe_load(ymlfile)

    # Parse state codes
    with open(path.join(template_path, 'state_codes.yaml'), 'r') as ymlfile:
        state_codes = yaml.safe_load(ymlfile)

    # Parse county codes
    with open(path.join(template_path, 'county_codes.yaml'), 'r') as ymlfile:
        county_codes = yaml.safe_load(ymlfile)

    # Parse country_lang
    with open(path.join(template_path, 'country2lang.yaml'), 'r') as ymlfile:
        country_lang = yaml.safe_load(ymlfile)

    abbreviations = {}
    abbv_path = path.join(template_path, 'abbreviations')

    abbv_files = filter(path.isfile, [path.join(abbv_path, f) for f in os.listdir(abbv_path)])
    for abbv_file in abbv_files:
        key = path.splitext(path.basename(abbv_file))[0].upper()
        with open(abbv_file, 'r') as ymlfile:
            abbreviations[key] = yaml.safe_load(ymlfile)

    return Config(components, component_aliases, templates, state_codes, county_codes, country_lang)
