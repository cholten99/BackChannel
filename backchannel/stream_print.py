#!/usr/bin/env python

import sys
import unicodedata
import pprint
from twitter import *

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

my_string = ""
for entity in user_iter:
  try:
    for entry in entity:
      value = entity.get(entry)
      value_to_print = ""
      the_type = type(value)
      if ((the_type == list) or (the_type == dict)):
        value_to_print = '[%s]' % ', '.join(map(str, value))
      elif (the_type == bool):
        if (value == True):
          value_to_print = "True"
        else:
           value_to_print = "False"
      elif (the_type == unicode):
        value_to_print = value.decode('unicode-escape')

      print entry + " = " + value_to_print
      if (entry == 'user'):
        print "user['screen_name'] = " + (entity.get('user')['screen_name']).decode('unicode-escape')
      elif (entry == 'source'):
        print "source['screen_name'] = " + (entity.get('source')['screen_name']).decode('unicode-escape')
      elif (entry == 'direct_message'):
        print "direct['sender_screen_name'] = " + (entity.get('direct_message')['sender_screen_name']).decode('unicode-escape')


    print "\n +++++ \n";

  except:    
    print "Unexpected error:", sys.exc_info()[0]

######

#TestyMcTest99

# First entity is always entity.get('friends') which returns an array of everyone being followed

# If someone you're following tweets, get screen_name with (entity.get('user')['screen_name']).decode('unicode-escape')

# Someone unfollowing you has no notification

# Someone following you has an attribute 'event' set to 'follow', get screen name with (entity.get('source')['screen_name']).decode('unicode-escape')

# Direct message has an entity called direct_message, get screen name 


