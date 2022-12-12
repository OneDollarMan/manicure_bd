import logging.config
import yaml
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5

logging.config.dictConfig(yaml.safe_load(open('logging/logging.conf')))
file_logger = logging.getLogger('file')
console_logger = logging.getLogger('console')

app = Flask(__name__, static_folder="static")
Bootstrap5(app)
app.config.from_object('config')
csrf = CSRFProtect(app)

import views
