""" core-api.py """

import resources.header
from flask import Flask, request, render_template, jsonify
from flask_restful import Resource, Api
from resources.concat import Concat
from resources.convert import Convert
from resources.extract import Extract
from resources.generate import Generate
from resources.separate import Separate
app = Flask(__name__)
api = Api(app)

@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

api.add_resource(Extract,'/extract/name=<string:name>&output=<string:output>')
api.add_resource(Convert,'/convert/name=<string:name>&typec=<string:typec>')
api.add_resource(Separate,'/separate/name=<string:name>')
api.add_resource(Concat,'/concat/name=<string:name>')
api.add_resource(Generate,'/generate/name=<name>')


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
