from os import path
import re
from functools import partial, reduce
import chevron
import yaml

REQUIRED_ADDRESS_COMPONENTS = [
    'road',
    'postcode'
]

VALID_REPLACEMENT_COMPONENTS = [
    'state'
]


def _dedup(splitter, input_string):
    coll = map(str.strip, input_string.split(splitter))
    seen_input_string = set()
    unique_strings = [s for s in coll if s and not (s in seen_input_string or seen_input_string.add(s))]
    return unique_strings


def _sanity_clean_address(addr_components):
    cleaned_addr_components = addr_components.copy()
    if cleaned_addr_components.get('postcode') and len(cleaned_addr_components['postcode']) > 20:
        del cleaned_addr_components['postcode']

    for k, v in cleaned_addr_components.items():
        if not v or re.match(r'https?:\/\/', v):
            del cleaned_addr_components[k]

    return cleaned_addr_components


def _has_minimum_address_components(addr_components):
    min_threshold = 2
    return sum([1 if addr_components.get(c) else 0 for c in REQUIRED_ADDRESS_COMPONENTS]) >= min_threshold


def _fix_country(addr_components):
    updated_addr_components = addr_components.copy()

    # is the country a number? if so, and there is a state, use state as country
    if updated_addr_components.get('country') and updated_addr_components.get('state') and \
            updated_addr_components['country'].isdecimal():
        updated_addr_components['country'] = updated_addr_components['state']
        del updated_addr_components['state']
    return updated_addr_components


def _apply_replacements(replacements, addr_component):
    if replacements is None:
        return addr_component

    updated_addr_component = addr_component.copy()
    for k, v in updated_addr_component.items():
        for replacement in replacements:
            matches = re.match(r'^{}=(.+)'.format(k), replacement[0])
            if matches:
                if matches[1] == v:
                    updated_addr_component[k] = replacement[1]
            else:
                updated_addr_component[k] = v.replace(*replacement)

    return updated_addr_component


def _add_state_code(state_codes, addr_components):
    need_update = not addr_components.get('state_code') and addr_components.get('state') \
                  and addr_components.get('country_code')
    if not need_update:
        return addr_components

    updated_addr_components = addr_components.copy()

    country_code = updated_addr_components['country_code']
    if state_codes.get(country_code):
        for k, v in state_codes[country_code].items():
            if updated_addr_components['state'].upper() == v.upper():
                updated_addr_components['state_code'] = k

    return updated_addr_components


def _find_and_add_unknown_components(components, component_aliases, addr_components):
    unknown_keys = filter(lambda k: k not in components and k not in component_aliases,
                          addr_components.keys())
    unknown_components = [addr_components[k] for k in unknown_keys]

    if not unknown_components:
        return addr_components

    # Add attention, but only if needed
    updated_addr_components = addr_components.copy()
    updated_addr_components['attention'] = ', '.join(unknown_components)
    return updated_addr_components


def _clean_rendered(text):
    replacements = [
        (r'[\},\s]+$', ''),
        (r'^[,\s]+', ''),
        (r',\s*,', ', '),       # multiple commas to one
        (r'[\t ]+,[\t ]+', ', '),     # one horiz whitespace behind comma
        (r'[\t ][\t ]+', ' '),        # multiple horiz whitespace to one
        (r'[\t ]\n', '\n'),        # horiz whitespace, newline to newline
        (r'\n,', '\n'),         # newline comma to just newline
        (r',,+', ','),          # multiple commas to one
        (r',\n', '\n'),         # comma newline to just newline
        (r'\n[\t ]+', '\n'),       # newline plus space to newline
        (r'\n\n+', '\n')        # multiple newline to one
    ]

    for regx_pattern, replacement in replacements:
        text = re.sub(regx_pattern, replacement, text)

    dedup_lines = []
    for line in _dedup('\n', text):
        dedup_words = _dedup(',', line)
        dedup_lines.append(', '.join(dedup_words))

    text = '\n'.join(dedup_lines).strip()

    # Return final cleaned text + extra final newline
    return text + '\n'


def _render(template_text, addr_components):
    def first(context, text, render):
        new_text = render(text, context)
        return next((x.strip() for x in new_text.split('||') if x.strip()), '')

    context = addr_components.copy()
    context['first'] = partial(first, context)

    text = _clean_rendered(chevron.render(template_text, context))

    if re.match(r'\w', text):
        return text

    # Just in case we dont have anything
    # TODO we probably need a better logic than this
    values = filter(None, map(str, addr_components.values))
    text = _clean_rendered(', '.join(values))
    return text


def _post_format_replace(text, replacements):
    dedup_text = ', '.join(_dedup(', ', text))
    for r in replacements:
        # re lib doesnt support $ backreference, so we need to replace $ with \
        formatted_to_replacement = re.sub(r'\$(\d)', r'\\\1', r[1])
        dedup_text = re.sub(r[0], formatted_to_replacement, dedup_text)
    return _clean_rendered(dedup_text)


class Address:
    def __init__(self, **kwargs):
        self._templates = {}
        self._component_aliases = {}
        self._components = {}
        self._state_codes = {}
        self._load_template()

        self._addr_components = {}
        all_known_components = list(self._components.keys()) + list(self._component_aliases.keys())
        if kwargs:
            self._addr_components.update((k, str(kwargs[k])) for k in set(kwargs).intersection(all_known_components))

        assert self._addr_components, \
            'Address is empty, please set one or more of the following components: {}'.format(
                ', '.join(sorted(all_known_components)))

    def _load_template(self):
        template_path = path.abspath(path.join(path.dirname(__file__), '..', 'address-formatter-templates', 'conf'))
        if not path.isdir(template_path):
            raise IOError('Address formatting templates path cannot be found.')

        # Parse components and component aliases
        with open(path.join(template_path, 'components.yaml'), 'r') as ymlfile:
            components = yaml.safe_load_all(ymlfile)

            for component in components:
                if 'aliases' in component:
                    self._component_aliases.update({alias: component['name'] for alias in component['aliases']})
                self._components[component['name']] = component.get('aliases')

        # Parse templates
        with open(path.join(template_path, 'countries', 'worldwide.yaml'), 'r') as ymlfile:
            self._templates = yaml.safe_load(ymlfile)

        # Parse state codes
        with open(path.join(template_path, 'state_codes.yaml'), 'r') as ymlfile:
            self._state_codes = yaml.safe_load(ymlfile)

    def _determine_country_code(self):
        cc = self._addr_components.get('country_code', '')
        if len(cc) != 2:
            return cc

        country_code = cc.upper()

        if country_code == 'UK':
            country_code = 'GB'

        # Check if the configuration tells us to use the configuration of another country
        # Used in cases of dependent territories like American Samoa (AS) and Puerto Rico (PR)
        if self._templates.get(country_code) and self._templates[country_code].get('use_country'):
            old_country_code = country_code
            country_code = self._templates[country_code]['use_country']

            if self._templates[old_country_code].get('change_country'):
                new_country = self._templates[old_country_code]['change_country']

                matches = re.match(r'\$(\w*)', new_country)
                if matches:
                    component = matches[1]
                    new_country = re.sub(r'\$' + component, self._addr_components.get(component, ''), new_country)

                self._addr_components['country'] = new_country

            if self._templates[old_country_code].get('add_component') and \
                    '=' in self._templates[old_country_code]['add_component']:
                key, val = self._templates[old_country_code]['add_component'].split('=')
                if key in VALID_REPLACEMENT_COMPONENTS:
                    self._addr_components[key] = val

        if country_code == 'NL' and self._addr_components.get('state'):
            if self._addr_components['state'] == 'Curaçao':
                country_code = 'CW'
                self._addr_components['country'] = 'Curaçao'
            elif re.match(r'^sint maarten', self._addr_components['state'], re.IGNORECASE):
                country_code = 'SX'
                self._addr_components['country'] = 'Sint Maarten'
            elif re.match(r'^Aruba', self._addr_components['state'], re.IGNORECASE):
                country_code = 'AW'
                self._addr_components['country'] = 'Aruba'

        return country_code

    def format(self, opts=None):
        country_code = opts['country'] if isinstance(opts, dict) and 'country' in opts \
            else self._determine_country_code()

        if country_code:
            country_code = country_code.upper()
            self._addr_components['country_code'] = country_code

        # Set the alias values (unless it would override something)
        for k, v in self._component_aliases.items():
            if self._addr_components.get(k) and not self._addr_components.get(v):
                self._addr_components[v] = self._addr_components[k]

        self._addr_components = _sanity_clean_address(self._addr_components)

        template = self._templates.get(country_code) or self._templates['default']
        template_text = template.get('address_template', '')

        # Do we have the minimal components for an address? or should we instead use the fallback template?
        if not _has_minimum_address_components(self._addr_components):
            if template.get('fallback_template'):
                template_text = template['fallback_template']
            elif self._templates['default'].get('fallback_template'):
                template_text = self._templates['default']['fallback_template']

        # Cleanup the components by applying list of cleanup functions
        self._addr_components = reduce(lambda components, func: func(components),
                                       [
                                           _fix_country,
                                           partial(_apply_replacements, template.get('replace')),
                                           partial(_add_state_code, self._state_codes),
                                           partial(_find_and_add_unknown_components, self._components,
                                                   self._component_aliases)
                                       ],
                                       self._addr_components)

        # Render the template
        text = _render(template_text, self._addr_components)

        # Post render cleanup
        if template.get('postformat_replace'):
            text = _post_format_replace(text, template['postformat_replace'])

        return text
