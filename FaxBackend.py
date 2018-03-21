#!/usr/bin/python

# FaxBackend.py
# Backend service runs in the background and processes the inbound faxes. Stores relevant
# information in a SQLite db.

import logging
import sys
import datetime
import yaml
import json
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, scoped_session
from exchangelib import Credentials, Account, DELEGATE, Configuration, Message, FileAttachment

engine = create_engine('sqlite:///faxprocessor.db', echo=False)
Base = declarative_base()

class Fax(Base):
    __tablename__ = 'Fax'
    
    id = Column(Integer, primary_key=True)
    subject = Column(String)
    message_id = Column(String)
    path_to_folder = Column(String)
    datetime_received = Column(DateTime, default=datetime.datetime.utcnow())
    to_recipient = Column(String)
    sender = Column(String)
    
    
Session = sessionmaker(bind=engine)
session = scoped_session(Session)
Base.metadata.create_all(engine)

def process_faxes(mail_server,fax_journal_account,fax_journal_password, fax_storage_repo):
    """
    Function to run through mailbox and process fax items
    """
    exchange_credentials = Credentials(username=fax_journal_account, password=fax_journal_password)
    exchange_conn_config = Configuration(server=mail_server, credentials=exchange_credentials)
    exchange_account = Account(primary_smtp_address=fax_journal_account, config=exchange_conn_config,
                               autodiscover=False, access_type=DELEGATE)
    datetime_today = datetime.datetime.strptime(str(datetime.datetime.utcnow()).split(" ")[0], "%Y-%m-%d").strftime("%d%m%Y")
    if not os.path.exists(os.path.join(fax_storage_repo,datetime_today)):
        print "Does not exist"
        os.makedirs(os.path.join(fax_storage_repo,datetime_today))
    for i in exchange_account.inbox.all():
        fax_info = {}
        fax_info['message_id'] = i.message_id
        fax_info['subject'] = i.subject
        fax_info['datetime_sent'] = str(i.datetime_sent)
        fax_info['to_recipient'] = i.to_recipients[0].email_address
        fax_info['datetime_received'] = str(i.datetime_received)
        fax_info['sender'] = i.sender.email_address
        
        fax_path = os.path.join(CONFIGURATION['fax_storage_repo'], datetime_today, fax_info['message_id'][1:-1])
        if not os.path.exists(fax_path):
            os.makedirs(fax_path)
        attachments_path = os.path.join(fax_path, 'attachments')
        if not os.path.exists(attachments_path):
            os.makedirs(os.path.join(fax_path, 'attachments'))
        meta_path = os.path.join(fax_path, 'meta.json')
        with open(meta_path, 'w') as outfile:
            json.dump(fax_info, outfile)
        for attachment in i.attachments:
            if isinstance(attachment, FileAttachment):
                attachment_path = os.path.join(attachments_path, attachment.name)
                with open(attachment_path, 'wb') as f:
                    f.write(attachment.content)
        encoded_html_body = i.body.encode('utf-8')
        html_body_path = os.path.join(fax_path, 'body.html')
        with open(html_body_path, 'wb+') as f:
            f.write(encoded_html_body)
        print fax_info['message_id']+" completed."
        if not session.query(Fax).filter(Fax.message_id == i.message_id).first():
            fax_sql_record = Fax(subject = fax_info['subject'],
                                 message_id = fax_info['message_id'],
                                 path_to_folder = fax_path,
                                 datetime_received = i.datetime_received,
                                 sender = fax_info['sender'],
                                 to_recipient = fax_info['to_recipient'])
            session.add(fax_sql_record)
    session.commit()
                                 



def main(CONFIGURATION):
    logging.basicConfig()
    print CONFIGURATION
    process_faxes(CONFIGURATION['mail_server'], CONFIGURATION['fax_journal_account'],
                  CONFIGURATION['fax_journal_password'], CONFIGURATION['fax_storage_repo'])
    #scheduler = BlockingScheduler()
    #scheduler.start()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as ymlfile:
            CONFIGURATION = yaml.load(ymlfile)
        main(CONFIGURATION)
    else:
        print "Need configuration file. E.G. config.yml"