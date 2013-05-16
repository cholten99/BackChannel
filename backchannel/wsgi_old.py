#!/usr/bin/env python

import time
import sys
import os
import json
import pprint
from time import gmtime, strftime
from flask import *
import MySQLdb
from twitter import *
application = app = Flask('wsgi')

@app.route('/')
def welcome():
  return "TEST2!"

@app.route('/mysql_test')
def mysql_test():

  con = mysql_connect()

  try:
    cursor = con.cursor()

http://www.mikusa.com/python-mysql-docs/query.html

    cursor.execute("INSERT INTO test VALUES ('slime', 'mold')")
    cursor.execute("SELECT * FROM test")
    the_string = ""
    for row in cursor.fetchall():
      the_string += row[0] + ", " + row[1] + "<br>"

    return the_string

  except:
    return "Unexpected error:", sys.exc_info()[0]

  finally:
    if con:
      con.close()

@app.route('/time_to_db')
def time_to_db():
  con = mysql_connect()

  time_text = "The data is : " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
#  while(os.environ["on_switch"] == "on"):
  cursor = con.cursor()
  cursor.execute("UPDATE test SET second_col='" + time_text + "' WHERE first_col='fish'")

#    time.sleep(1)

  # Never gets here
  return "Switched off"

def mysql_connect():
  try:
    services_data = os.environ.get("VCAP_SERVICES")
    if (not services_data):
      return MySQLdb.connect("localhost","test","test","test")
    else:
      services = json.loads(os.environ.get("VCAP_SERVICES"))
      services = services["mysql-5.1"][0]["credentials"]
      return MySQLdb.connect(services["hostname"], services["username"], services["password"], "test")

  except:
    return "Unexpected error:", sys.exc_info()[0]

@app.route('/on_switch_value')
def on_switch_value():
  return os.environ.get("on_switch")

@app.route('/toggle')
def toggle():
  if (os.environ["on_switch"] != "on"):
    os.environ["on_switch"]="on"
  else:
    os.environ["on_switch"]="off"
  return os.environ["on_switch"]

if __name__ == '__main__':
  app.run(debug=True)

  url_for('static', filename='test_page.html')
  url_for('static', filename='flip_switch.html')
  url_for('static', filename='flip_switch.css')

"""
@app.route('/get_data')
def get_data():

  access_token = "1398779173-A16HgEAmp2Ijqfl99hueBkiZ6kevgCnQx3DEbHe"
  access_secret = "FstWuWDUWsmMwbIkdV1bTo9PnPSdFwzYishpCnpPUU"
  consumer_key = "MMwfjb0YBiDgsOkU3jnYNA"
  consumer_secret = "UQJZscP2JcPni9rIxHQBA6CAbp9rE43Zg4EUtUMsdI"

  # create twitter API object
  auth = OAuth(access_token, access_secret, consumer_key, consumer_secret)
  twitter = Twitter(auth = auth)

  # Testing user streaming
  stream = TwitterStream(domain = "userstream.twitter.com", auth = auth, api_version = 2, secure = True)
  user_iter = stream.user()

  # !!!
  # !!! Surely every time the HTML reconnects this creates a new stream connection to the server!
  # !!!
  # !!! Fix with this : http://flask.pocoo.org/docs/patterns/streaming/
  # !!!
  my_string = ""
  for entity in user_iter:
    try:
      my_string = str(entity)
    except:    
      my_string = "Unexpected error:", sys.exc_info()[0]

    return my_string
"""

"""
  # Test sending a DM
  target = "cholten99"
  dm_text = "The time sponsored by me is : " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
  result = twitter.direct_messages.new(screen_name = target, text = dm_text)

  return "Done it!"
"""

"""
  # Follows and following
  # twitter API docs: https://dev.twitter.com/docs/api/1/get/friendships/show
  source = "_BackChannel_"
  target = "cholten99"
  result = twitter.friendships.show(source_screen_name = source, target_screen_name = target)
  # extract the relevant properties
  following = result["relationship"]["target"]["following"]
  follows   = result["relationship"]["target"]["followed_by"]

  return_string = "%s following %s: %s" % (source, target, follows) + "<p>"
  return_string += "%s following %s: %s" % (target, source, following)

  return return_string
"""

"""
  # Post a test update
  results = twitter.statuses.update(status = "Testy testy mctest")

  return "Done it!"
"""

"""
  # Get a user's timeline
  # twitter API docs: https://dev.twitter.com/docs/api/1/get/statuses/user_timeline
  user = "cholten99"

  results = twitter.statuses.user_timeline(screen_name = user)

  # loop through each of the statuses, and print its content
  return_string = ""
  for status in results:
    return_string += "(%s) %s" % (status["created_at"], status["text"]) + "<p>"

  return return_string
"""

"""

1) Every user needs to be able to do 3 types of list (i) list channels they own, (ii) list channels they belong to, (iii) list who is in a given channel
2) Every time someone is added or removed from a channel everyone is notified
3) No-one can be added to a channel without their permission
4) A user can leave a channel at any time and also be booted by the owner

1) A user can:
  (i) Find out what channels they subscribe to / have been invited to
  (ii) Find out who is on a channel they are a member of
  (iii) Join a channel they have been invited to
  (iv) Leave a channel they are a member of
  (v) Broadcast to a channel they are a member of
  (vi) Get help

2) An owner is a user but also can:
  (i) List channels they own
  (ii) Create a channel (including initial invite list)
  (iii) Invite new people to channel they own
  (iv) Remove someone from a channel they own
  
3) Questions / Notes:
  (i) What if someone followed @_BackChannel_ ? Automatically follow them back?
  (ii) Follow someone (if not following them already) when sending them an invite to a channel?
  (iii) What to do if someone is invited to a list but doesn't follow _@BackChannel_? *Don't* tweet to invite them to join as is then public. Just inform channel owner.
  (iv) If @_BackChannel_ is tweeted to just reply with a "How To" URL
  (v) Have the option of doing all the owner tasks via the website (log in with Twitter to do so)
  (vi) How long does the hashtag need to be?
  (vii) Note : actual broadcast DM information is _not_ stored

Database:
  (i) Channel : UID, hastag, owner_screen_name
  (ii) People : UID, screen_name, hashtag, member (binary, false if just invited)

Notes:
1) It's @_BackChannel_ 
2) Twitter's page on the streaming API : http://goo.gl/xofKC
3) Twitter library API : http://mike.verdone.ca/twitter/
4) Twitter developer API console : https://dev.twitter.com/console
"""
