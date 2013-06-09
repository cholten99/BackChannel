#!/usr/bin/env python

import sys
import unicodedata
import pprint
import urllib2
from twitter import *
import MySQLdb
import logging
from time import gmtime, strftime
from random import randint

# Use the below to help with debugging
# import traceback
# traceback.print_stack(file=sys.stdout)

## FOR DEBUGGING  
def debug_entity(entity):
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

# Function to output to the log
def log_string(output):
  log_string = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " : " + output
  logging.info(log_string)

# Attempt to broadcast to everyone on the given channel (check it's defined)
def do_broadcast(screen_name, parts, hashtags, ats):
  parts.insert(0, "@" + screen_name)  
  dm_text = " ".join(parts)
  broadcast(screen_name, hashtags[0], dm_text)

# Function to DM passed-in text to everyone on a channel
def broadcast(screen_name, channel, text):
  cursor.execute("SELECT screen_name FROM users WHERE channel_hashtag='%s' AND member='%s'" %(channel, 1))
  for row in cursor.fetchall():
    if (row[0] != screen_name):
      dm(row[0], text)

# Function to DM passed-in text to supplied user
# Nb handles messages > 140 chars by splitting into chunks
def dm(screen_name, dm_text):
  while (True):
    if (len(dm_text) <= 140):
      log_string("DMing (<140 chars) %s with %s" % (screen_name, dm_text))
      twitter.direct_messages.new(screen_name = screen_name, text = dm_text)
      break
    else:
      end_pos = dm_text.rfind(" ", 0, 140)
      send_text = dm_text[0:end_pos]
      dm_text = dm_text[end_pos+1:]
      log_string("DMing (>140 chars) %s with %s" % (screen_name, dm_text))
      twitter.direct_messages.new(screen_name = screen_name, text = dm_text)

# Function to check whether a given user is a member of a channel
def is_member(screen_name, channel):
  rows_returned = cursor.execute("SELECT screen_name FROM users WHERE screen_name='%s' AND channel_hashtag='%s' AND member=1" % (screen_name, channel))
  if (rows_returned == 0):
    return None
  else:
    row = cursor.fetchone()
    return row[0]

# Function to check whether a given user is invited to a channel
def is_invited(screen_name, channel):
  rows_returned = cursor.execute("SELECT screen_name FROM users WHERE screen_name='%s' AND channel_hashtag='%s' AND member=0" % (screen_name, channel))
  if (rows_returned == 0):
    return None
  else:
    row = cursor.fetchone()
    return row[0]

# Function to check whether a given user owns a channel
def is_owner(screen_name, channel):
  rows_returned = cursor.execute("SELECT UID FROM channels WHERE owner_screen_name='%s' AND hashtag='%s'" % (screen_name, channel))
  if (rows_returned == 0):
    return None
  else:
    return screen_name

# Function to return "don't understand" to a user
def dont_understand(screen_name):
  dm_text = "Sorry, I don't understand, for help - see http://stuff.thing"
  number_spaces = randint(1,79)
  dm_text += (" " * number_spaces)
  dm(screen_name, dm_text)

# Function to check whether a given user follows BackChannel
def is_following(screen_name):
  result = twitter.friendships.show(source_screen_name = '_BackChannel_', target_screen_name = screen_name)
  return_value = result["relationship"]["target"]["followed_by"]
  return(return_value)

# Function to process incoming tweets or DMs
def process_message(message):
  hashtags = []
  ats = []
  parts = message.split()
  for part in parts:
    if (part[0] == '#'):
      hashtags.append(part)
    if (part[0] == '@'):
      ats.append(part)
  return parts, hashtags, ats

# Function to process incomming DMs
def process_dm(screen_name, parts, hashtags, ats):
  # Okay, now we're down to the good stuff
  first_word = parts[0]
  if (first_word == 'list'):
    do_list(screen_name, parts, hashtags, ats)
  elif (first_word == 'new'):
    do_new(screen_name, parts, hashtags, ats)
  elif (first_word == 'kill'):
    do_kill(screen_name, parts, hashtags, ats)
  elif (first_word == 'add'):
    do_add(screen_name, parts, hashtags, ats)
  elif (first_word == 'boot'):
    do_boot(screen_name, parts, hashtags, ats)
  elif (first_word == 'join'):
    do_join(screen_name, parts, hashtags, ats)
  elif (first_word == 'leave'):
    do_leave(screen_name, parts, hashtags, ats)
  else:
    # It's not a command so we see if we should broadcast it
    if (len(hashtags) == 0):
      dont_understand(screen_name)
    else:
      if (is_member(screen_name, hashtags[0]) is not None):
        do_broadcast(screen_name, parts, hashtags, ats)
      else:
        dont_understand(screen_name)

# Either list channels I own, channels I'm in, channels I'm invited to or people in a given 
# channel depending on rest of message (only list if it's a channel the person is in)
def do_list(screen_name, parts, hashtags, ats):
  if (len(parts) > 2):
    dont_understand(screen_name)
  elif (len(parts) == 1):
    # It's just 'list'
    # Channels owned  
    num_rows = cursor.execute("SELECT hashtag FROM channels WHERE owner_screen_name='%s'" % (screen_name))
    if (num_rows == 0):
      dm(screen_name, "You do not own any channels")
    else:
      owner_string = "You own the following channels: "
      for row in cursor.fetchall():
        owner_string += row[0] + ", "
      owner_string = owner_string[:-2]
      dm(screen_name, owner_string)
    # Channels a member of
    num_rows = cursor.execute("SELECT channel_hashtag FROM users WHERE (screen_name='%s' AND member=1)" % (screen_name))
    if (num_rows == 0):
      dm(screen_name, "You are not a member of any channels")
    else:
      member_string = "You are a member of the following channels: "
      for row in cursor.fetchall():
        member_string += row[0] + ", "
      member_string = member_string[:-2]
      dm(screen_name, member_string)
    # Channels invited to
    num_rows = cursor.execute("SELECT channel_hashtag FROM users WHERE (screen_name='%s' AND member=0)" % (screen_name))
    if (num_rows == 0):
      dm(screen_name, "You are not currently invited to any channels")
    else:
      invited_string = "You are currently invited to the following channels: "
      for row in cursor.fetchall():
        invited_string += row[0] + ", "
      invited_string = invited_string[:-2]
      dm(screen_name, invited_string)
  else:
    # There's two parameters
    if (len(hashtags) != 1):
      dont_understand(screen_name)
    else:
      if (not is_member(screen_name, hashtags[0])):
        # They're not a member of the specified channel
        dont_understand(screen_name)
      else:
        channel = hashtags[0]
        num_rows = cursor.execute("SELECT screen_name FROM users WHERE channel_hashtag='%s'" % (channel))
        members_string = "The members of channel " + channel + " are "
        for row in cursor.fetchall():
          members_string = "@" + row[0] + ", "
        members_string = members_string[:-2]
        dm(screen_name, members_string)

# Create a new channel using a random word.
def do_new(screen_name, parts, hashtags, ats):
  if (len(parts) > 1):
    dont_understand(screen_name)
  else:
    new_hashtag = "#" + urllib2.urlopen("http://randomword.setgetgo.com/get.php").read()
    new_hashtag = new_hashtag[4:-2]
    new_hashtag = '#' + new_hashtag
    cursor.execute("INSERT INTO channels (hashtag, owner_screen_name) VALUES ('%s', '%s')" % (new_hashtag, screen_name))
    cursor.execute("INSERT INTO users (screen_name, channel_hashtag, member) VALUES ('%s', '%s', '%s')" % (screen_name, new_hashtag, '1'))
    con.commit()
    dm(screen_name, "New channel created called " + new_hashtag)

# Attempt to destroy an existing channel. Must be owner. DM all current members to say 'going down'
def do_kill(screen_name, parts, hashtags, ats):
  if (len(hashtags) == 0):
    dont_understand(screen_name)
  else:
    channel = hashtags[0]
    check_owner = is_owner(screen_name, channel)
    if (check_owner is None):
      # Channel not owned by user or doesn't exist
      dont_understand(screen_name)
    else:
      # Inform all the full members
      broadcast(screen_name, channel, "@" + screen_name + " has closed channel " + channel)
      dm(screen_name, "Channel " + channel + " has been removed")
      # Remove from DB
      cursor.execute("DELETE from users WHERE channel_hashtag='%s'" % (channel))
      cursor.execute("DELETE from channels WHERE hashtag='%s'" % (channel))
      con.commit()

# Attempt to add potentially multiple people to an existing channel. Must be owner.
# They musy be followers. DM failure or DM owner to say they've been invited.
def do_add(screen_name, parts, hashtags, ats):
  if (len(hashtags) == 0):
    dont_understand(screen_name)
  else:
    channel = hashtags[0]
    if (len(ats) == 0):
      dont_understand(screen_name)
    else:
      # Check if already a member
      member_list = []
      invited_list = []
      not_following_list = []
      for at in ats:
        if (is_member(at, channel)):
          member_list.append(at)
        elif (is_invited(at, channel)):
          invited_list.append(at)
        elif (not is_following(at)):
          not_following_list.append(at)
      ats = [x for x in ats if x not in member_list]
      ats = [x for x in ats if x not in invited_list]
      ats = [x for x in ats if x not in not_following_list]
      if (len(member_list) != 0):
        member_string = "Unable to invite following as they are already members: "
        for member in member_list:
          member_string += member + ", "
        member_string[:-2]
        dm(screen_name, member_string)
      if (len(invited_list) != 0):
        invited_string = "Unable to invite following as they are already invited to " + channel + ": "
        for invited in invited_list:
          invited_string += invited + ", "
        invited_string[:-2]
        dm(screen_name, invited_string)
      if (len(not_following_list) != 0):
        not_following_string = "Unable to invite following as they are not following @_BackChannel_: "
        for not_following in not_following_list:
          not_following_string += not_following + ", "
        not_following_string[:-2]
        dm(screen_name, not_following_string)
      new_string = "Invited the following to join " + channel + ": "
      for invitee in ats:
        invitee = invitee[1:]
        cursor.execute("INSERT INTO users (screen_name, channel_hashtag, member) VALUES ('%s', '%s', 0)" % (invitee, channel))
        con.commit()
        dm(invitee, screen_name + " has invited you to join channel " + channel)
        new_string += invitee + ", "
      new_string = new_string[:-2]
      dm(screen_name, new_string)

# Attempt to boot someone off a channel, DM failure back or remove and DM person gone and all left
def do_boot(screen_name, parts, hashtags, ats):
  if (len(hashtags) == 0):
    dont_understand(screen_name)
  else:
    channel = hashtags[0]
    if (len(ats) != 1):
      dont_understand(screen_name)
    else:
      bootee = ats[0][1:] # Strip '@' off the front
      check_member = is_member(bootee, channel)
      check_invited = is_invited(bootee, channel)
      if ((check_member is None) and (check_invited is None)):
        # Can't boot a non-member
        dont_understand(screen_name)
      else:
        cursor.execute("DELETE FROM users WHERE channel_hashtag='%s' AND screen_name='%s'" % (channel, bootee))
        con.commit()
        if (check_member is None):
          # They were only at the invite stage
          dm(screen_name, "@" + bootee + " has been de-invited from channel " + channel)
          dm(bootee, "You have been de-invited from channel " + channel)
          broadcast(screen_name, channel, "@" + screen_name + " has de-invited @" + bootee + "from channel " + channel)
        else:
          # They were a full member
          dm(bootee, "@" + screen_name + " has removed you from channel " + channel)
          dm(screen_name, "@" + bootee + " has been removed from channel " + channel)
          broadcast(screen_name, channel, "@" + screen_name + " has removed @" + bootee + "from channel " + channel)

# Attempt to join an existing channel, check if they have been invited, if successful
# DM all existing member of the list saying they joined and reply to them
def do_join(screen_name, parts, hashtags, ats):
  if (len(hashtags) == 0):
    dont_understand(screen_name)
  else:
    channel = hashtags[0]
    check_member = is_member(screen_name, channel)
    if (check_member is not None):
      dm(screen_name, "You are already a member of channel " + channel)
    check_invited = is_invited(screen_name, channel)
    if (check_invited is None):
      # They've never even been invited
      dont_understand(screen_name)
    else:
      cursor.execute("UPDATE users SET member=1 WHERE screen_name='%s' AND channel_hashtag='%s'" % (screen_name, channel))
      con.commit()
      broadcast(screen_name, channel, "Please welcome " + screen_name + " to channel " + channel)
      dm(screen_name, "You have successfully joined channel " + channel)
        
# Attempt to leave an existing channel, check they're a member, DM all current members 
# to say they've left and DM they to say left
def do_leave(screen_name, parts, hashtags, ats):
  if (len(hashtags) == 0):
    dont_understand(screen_name)
  else:
    channel = hashtags[0]
    check_member = is_member(screen_name, channel)
    check_invited = is_invited(screen_name, channel)
    if ((check_member is None) and (check_invited is None)):
      # They're not a member or invited to that channel
      dont_understand(screen_name)
    else:
      cursor.execute("DELETE FROM users WHERE channel_hashtag='%s' AND screen_name='%s'" % (channel, screen_name))
      con.commit()
      if (check_member is not None):
        # They were a full member
        dm(screen_name, "You have left channel " + channel)
        broadcast(screen_name, channel, "@" + screen_name + " has left channel " + channel)
      else:
        # They were a pending member
        dm(screen_name, "Pending request for channel " + channel + " has been removed")
        broadcast(screen_name, channel, "@" + screen_name + " has declined to join channel " + channel)

# MAIN

# Set up logging
logging.basicConfig(filename='/home/dave/Development/BackChannel/backchannel/backchannel.txt',level=logging.DEBUG)
log_string(">>> RESTART <<<")

# Oauth tokens
access_token = "1398779173-A16HgEAmp2Ijqfl99hueBkiZ6kevgCnQx3DEbHe"
access_secret = "FstWuWDUWsmMwbIkdV1bTo9PnPSdFwzYishpCnpPUU"
consumer_key = "MMwfjb0YBiDgsOkU3jnYNA"
consumer_secret = "UQJZscP2JcPni9rIxHQBA6CAbp9rE43Zg4EUtUMsdI"

# create twitter API object
auth = OAuth(access_token, access_secret, consumer_key, consumer_secret)
twitter = Twitter(auth = auth)

# Connect to the database
con = MySQLdb.connect("localhost","cholten99","cholten99","backchannel")
cursor = con.cursor()

# Testing user streaming
stream = TwitterStream(domain = "userstream.twitter.com", auth = auth, api_version = 2, secure = True)
user_iter = stream.user()

# ENDLESS EVENT PROCESSING LOOP STARTS HERE!
for entity in user_iter:
  # Uncomment to debug incoming events
  # debug_entity(entity)

  if ('event' in entity):
    if (entity.get('event') == 'follow'):
      # It's a follow, so we follow back (if we're not doing so already) and DM they to say hi      
      screen_name = (entity.get('source')['screen_name']).decode('unicode-escape')
      if (screen_name != "_BackChannel_"):
        if (not is_follower(screen_name)):
          twitter.friendships.create(screen_name = screen_name)
        dm_text = "Hi " + screen_name + ", welcome to BackChannel, have a read of the instructions : http://stuff.thing"
        dm(screen_name, dm_text)
  elif ('direct_message' in entity):
    # Okay, it's a DM so we're in business
    screen_name = (entity.get('direct_message')['sender_screen_name']).decode('unicode-escape')
    # Very weirdly when we send a DM it sends us a copy back to ourselves so skip those
    if (screen_name == "_BackChannel_"):
      continue
    text = (entity.get('direct_message')['text']).decode('unicode-escape')
    parts, hashtags, ats = process_message(text)
    process_dm(screen_name, parts, hashtags, ats)

"""
# NOTES #

Test account : @TestyMcTest99

CREATE TABLE IF NOT EXISTS `channels` (
  `UID` int(11) NOT NULL auto_increment,
  `hashtag` varchar(50) NOT NULL,
  `owner_screen_name` varchar(50) NOT NULL,
  PRIMARY KEY  (`UID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

CREATE TABLE IF NOT EXISTS `users` (
  `UID` int(11) NOT NULL auto_increment,
  `screen_name` varchar(50) NOT NULL,
  `channel_hashtag` varchar(50) NOT NULL,
  `member` tinyint(1) NOT NULL,
  PRIMARY KEY  (`UID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

grant all on backchannel.* to cholten99@localhost;
set password for cholten99@localhost = password('cholten99');


"""
