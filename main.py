from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app,
     origins=[
         "http://localhost:5173",
         "http://127.0.0.1:5173"
     ],
     supports_credentials=True
)
app.config.from_pyfile('config.py')

host = app.config['DB_HOST']
database = app.config['DB_NAME']
user = app.config['DB_USER']
password = app.config['DB_PASSWORD']

from usuario import *
from projeto import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
