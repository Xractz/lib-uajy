from flask import Flask
from flask_cors import CORS
from src.SetUp import SetUp

app = Flask(__name__)
CORS(app)

setup = SetUp(app)
setup.run()

if __name__ == '__main__':
    app.run()