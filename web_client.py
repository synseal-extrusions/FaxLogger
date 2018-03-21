from flask import Flask, render_template, jsonify
from sqlalchemy import *
from sqlalchemy import Column, Integer, String, Table
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, mapper
import datetime
 
app = Flask(__name__)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Fax(object):
    pass

engine = create_engine('sqlite:///faxprocessor.db', echo=True)
metadata = MetaData(engine)
fax_table = Table('Fax', metadata, autoload=True)
mapper(Fax, fax_table)

Session = sessionmaker(bind=engine)
session = Session()

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/api/fax')
def get_fax():
    results = session.query(Fax).all()
    data = {'data': []}
    for i in results:
        fax_item = {}
        fax_item['id'] = i.id
        fax_item['subject'] = i.subject
        fax_item['message_id'] = str(i.message_id)[1:-1]
        fax_item['path_to_folder'] = i.path_to_folder
        fax_item['datetime_received'] = i.datetime_received
        fax_item['to_recipient'] = i.to_recipient
        fax_item['sender'] = i.sender
        data['data'].append(fax_item)
    return jsonify(data['data'])
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)