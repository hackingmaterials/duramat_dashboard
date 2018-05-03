

import os

import dash
import dash_auth
import matplotlib
from pymongo import MongoClient

# needed for heroku deployment
matplotlib.use('Agg')

# instantiate app
users_passwords = [[os.environ.get('DURAMAT_DASH_USER'), os.environ.get('DURAMAT_DASH_PASS')]]
app = dash.Dash('auth')
auth = dash_auth.BasicAuth(app, users_passwords)
app.config.suppress_callback_exceptions = True
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

# Connect MongoDB
user = os.environ.get('MONGOD_DURAMAT_USER')
passwd = os.environ.get('MONGOD_DURAMAT_PASS')
leftover = os.environ.get('MONGOD_DURAMAT_LEFTOVER')
client = MongoClient('mongodb+srv://{}:{}@{}'.format(user, passwd, leftover))

server = app.server
