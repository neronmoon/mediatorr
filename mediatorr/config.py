import os

from mediatorr.utils.file import parse_yaml_file
from dotenv import load_dotenv

load_dotenv()

APP_DIR = os.path.dirname(os.path.realpath(__file__ + '/../'))
CONFIG_DIR = APP_DIR + '/config'

app = parse_yaml_file(CONFIG_DIR + '/app.yml')
local_config = CONFIG_DIR + '/app.local.yml'
if os.path.exists(local_config):
    app.update(parse_yaml_file(local_config))
