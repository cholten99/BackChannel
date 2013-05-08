#!/usr/bin/env python

import time
import sys
import os
import json
import pprint
from flask import Flask, Request, Response
import MySQLdb
application = app = Flask('wsgi')

@app.route('/')
def welcome():
  return "Today's fish!"

@app.route('/env')
def env():
  services_data = os.environ.get("VCAP_SERVICES")
  if (not services_data):
    return "Local"
  else:
    return services_data

@app.route('/mysql_test')
def mysql_test():

  con = mysql_connect()

  try:
    con.query("SELECT VERSION()")
    result = con.use_result()
    return "MySQL version: %s" % result.fetch_row()[0]

  except:
    return "Unexpected error:", sys.exc_info()[0]

  finally:
    if con:
      con.close()

def mysql_connect():
  try:
    if (env() == "Local"):
      return MySQLdb.connect("localhost","test","test","test")
    else:
      services = json.loads(os.environ.get("VCAP_SERVICES"))
      services = services["mysql-5.1"][0]["credentials"]
      return MySQLdb.connect(services["hostname"], services["username"], services["password"], "test")

  except:
    return "Unexpected error:", sys.exc_info()[0]

if __name__ == '__main__':
    app.run(debug=True)
