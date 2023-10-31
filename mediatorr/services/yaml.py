import warnings
import ruamel.yaml
import re
import os

from ruamel.yaml.error import ReusedAnchorWarning


class Yaml:
    _is_configured = False
    false_values = ['false', '0', '']

    @staticmethod
    def _configure():
        if not Yaml._is_configured:
            warnings.simplefilter("ignore", ReusedAnchorWarning)
            ruamel.yaml.SafeLoader.add_constructor('!ENV', Yaml._parse_env_tag)
            ruamel.yaml.SafeLoader.add_constructor('!BOOL', Yaml._parse_bool_tag)
            ruamel.yaml.SafeLoader.add_constructor('!INT', Yaml._parse_int_tag)
            Yaml._is_configured = True

    @staticmethod
    def _parse_env_tag(loader, node):
        pattern = re.compile(r'.*?\${(.*?)}.*?')
        node.value = {
            ruamel.yaml.ScalarNode: loader.construct_scalar,
            ruamel.yaml.SequenceNode: loader.construct_sequence,
            ruamel.yaml.MappingNode: loader.construct_mapping,
        }[type(node)](node)
        value = node.value
        match = pattern.findall(value)  # to find all env variables in line
        if match:
            full_value = value
            for group in match:
                splitted = group.split('|')
                types = ['str', 'bool', 'int']
                if len(splitted) == 1:
                    variable = group
                    default = ''
                    cast_to = 'str'
                else:
                    variable = splitted[0]
                    default = splitted[1] if splitted[1] not in types else ''
                    cast_to = splitted.pop()
                full_value = full_value.replace('${%s}' % group, os.environ.get(variable, default))
                if cast_to == 'bool':
                    full_value = full_value not in Yaml.false_values
                elif cast_to == 'int':
                    full_value = int(full_value)
            return full_value
        return value

    @staticmethod
    def _parse_bool_tag(loader, node):
        node.value = {
            ruamel.yaml.ScalarNode: loader.construct_scalar,
            ruamel.yaml.SequenceNode: loader.construct_sequence,
            ruamel.yaml.MappingNode: loader.construct_mapping,
        }[type(node)](node)

        return node.value.lower() not in Yaml.false_values

    @staticmethod
    def _parse_int_tag(loader, node):
        node.value = {
            ruamel.yaml.ScalarNode: loader.construct_scalar,
            ruamel.yaml.SequenceNode: loader.construct_sequence,
            ruamel.yaml.MappingNode: loader.construct_mapping,
        }[type(node)](node)
        return int(node.value)

    @staticmethod
    def parse(raw_content):
        Yaml._configure()
        return dict(ruamel.yaml.load(raw_content, Loader=ruamel.yaml.SafeLoader)).copy()

    @staticmethod
    def dump(data):
        Yaml._configure()
        return ruamel.yaml.dump(data)
