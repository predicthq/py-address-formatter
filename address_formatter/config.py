from os import path
from namedlist import namedtuple
import yaml

Config = namedtuple('Config', ['components', 'component_aliases', 'templates', 'state_codes'])


def load_config(template_path):
    templates = {}
    components = {}
    component_aliases = {}
    state_codes = {}

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

    return Config(components, component_aliases, templates, state_codes)
