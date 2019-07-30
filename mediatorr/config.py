import os

from mediatorr.utils.file import parse_yaml_file

APP_DIR = os.path.dirname(os.path.realpath(__file__ + '/../'))
CONFIG_DIR = APP_DIR + '/config'

app = parse_yaml_file(CONFIG_DIR + '/app.yml')
