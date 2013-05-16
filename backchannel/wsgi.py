#!/usr/bin/env python

import time
import sys
import os
import json
import pprint
from time import gmtime, strftime
from flask import *
import MySQLdb
from flaskext.mysql import MySQL
from twitter import *
application = app = Flask('wsgi')

@app.route('/')
def welcome():
  return "TEST2!"

@app.route('/mysql_test')
def mysql_test():
  db = mysql.get_db()
  cursor = db.cursor()

  while(True):
    time_text = "The data is : " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
    cursor.execute("UPDATE test SET second_col='" + time_text + "' WHERE first_col='test'")
    db.commit()
    time.sleep(1)

  return "Fish"

@app.route('/twitter_test')
def twitter_test():
  access_token = "1398779173-A16HgEAmp2Ijqfl99hueBkiZ6kevgCnQx3DEbHe"
  access_secret = "FstWuWDUWsmMwbIkdV1bTo9PnPSdFwzYishpCnpPUU"
  consumer_key = "MMwfjb0YBiDgsOkU3jnYNA"
  consumer_secret = "UQJZscP2JcPni9rIxHQBA6CAbp9rE43Zg4EUtUMsdI"

  # Get the database
  db = mysql.get_db()
  cursor = db.cursor()

  # create twitter API object
  auth = OAuth(access_token, access_secret, consumer_key, consumer_secret)
  twitter = Twitter(auth = auth)

  # Testing user streaming
  stream = TwitterStream(domain = "userstream.twitter.com", auth = auth, api_version = 2, secure = True)
  user_iter = stream.user()

  my_string = ""
  for entity in user_iter:
    try:
#      my_string = type(entity).__name__
      the_array = dir(entity)
      for entry in the_array:
        cursor.execute("INSERT INTO test VALUES('" + entry + "', 'goldfish')")
      db.commit()
    except:    
      return "Unexpected error:", sys.exc_info()[0]

  return "d'oh"

if __name__ == '__main__':
  app.config.update(
#    MYSQL_DATABASE_HOST
    MYSQL_DATABASE_USER = 'test',
    MYSQL_DATABASE_PASSWORD = 'test',
    MYSQL_DATABASE_DB = 'test'
  )
  mysql = MySQL()
  mysql.init_app(app)
  app.run(debug = True)
