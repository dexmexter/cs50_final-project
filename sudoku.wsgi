venv = '/var/www/cs50/venv/bin/activate_this.py'
with open(venv) as file_:
    exec(file_.read(), dict(__file__=venv))

import sys
sys.path.insert(0, '/var/www/cs50/')

from app import app as application
