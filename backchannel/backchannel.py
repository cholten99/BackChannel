#!/usr/bin/env python

import sys
import unicodedata
import pprint
import urllib2
import twitter
import MySQLdb

# Oauth tokens
access_token = "1398779173-A16HgEAmp2Ijqfl99hueBkiZ6kevgCnQx3DEbHe"
access_secret = "FstWuWDUWsmMwbIkdV1bTo9PnPSdFwzYishpCnpPUU"
consumer_key = "MMwfjb0YBiDgsOkU3jnYNA"
consumer_secret = "UQJZscP2JcPni9rIxHQBA6CAbp9rE43Zg4EUtUMsdI"

# Connect to the database
con = MySQLdb.connect("localhost","cholten99","cholten99","backchannel")
cursor = con.cursor()

# create twitter API object
auth = OAuth(access_token, access_secret, consumer_key, consumer_secret)
twitter = Twitter(auth = auth)

# Testing user streaming
stream = TwitterStream(domain = "userstream.twitter.com", auth = auth, api_version = 2, secure = True)
user_iter = stream.user()

# Loop forever and process each new event
for entity in user_iter:
  if ('friends' in entity):
    # It's the first time around, ignore it
    continue
  elif ('source' in entity):
    # It's a follow, so we follow back (if we're not doing so already) and DM they to say hi    
    screen_name = (entity.get('source')['screen_name']).decode('unicode-escape')
    if (not follower(screen_name)):
      twitter.friendships.create(screen_name = screen_name)
    dm_text = "Hi " + screen_name + ", welcome to BackChannel, have a read of the instructions : http://stuff.thing"
    dm(screen_name, dm_text)
  elif ('user' in entity):
    # This is a tweet from someone we follow, which could be a _lot_ of people
    # Since it could be nothing to do with us we only respond when there's an @_backchannel_
    # In that case we just respond with a link to a how-to page
    screen_name = (entity.get('user')['screen_name']).decode('unicode-escape')
    parts, hashtags, ats = process_message(entity.get('text'))
    if ('@_backchannel_' in parts):
      status_update = "@" + screen_name + " To use BackChannel have a read of the instructions : http://stuff.thing"
      results = twitter.statuses.update(status = status_update)
  elif ('direct_message' in entity):
    # Okay, it's a DM so we're in business
    screen_name = (entity.get('direct_message')['sender_screen_name']).decode('unicode-escape')
    text = (entity.get('direct_message')['text']).decode('unicode-escape')
    parts, hashtags, ats = process_message(text)
    process_dm(screen_name, parts, hashtags, ats)

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
  # Done
  elif (first_word == 'new'):
    do_new(screen_name, parts, hashtags, ats)
  # Done
  elif (first_word == 'kill'):
    do_kill(screen_name, parts, hashtags, ats)
  elif (first_word == 'add'):
    do_add(screen_name, parts, hashtags, ats)
  # Done
  elif (first_word == 'boot'):
    do_boot(screen_name, parts, hashtags, ats)
  # Done
  elif (first_word == 'join'):
    do_join(screen_name, parts, hashtags, ats)
  # Done
  elif (first_word == 'leave'):
    do_leave(screen_name, parts, hashtags, ats)
  # Done
  else:
    # It's not a command so we see if we should broadcast it
    # Check we have a channel
    if (len(hashtags) == 0):
      dont_understand(screen_name)
    else:
      if (is_member(screen_name, hashtags[0]) == True):
        do_broadcast(screen_name, parts, hashtags, ats)
      else:
        dont_understand(screen_name)

# NO LIST THEM ALL!
# Either list channels I own, channels I'm in, channels I'm invited to or people in a given 
# channel depending on rest of message (only list if it's a channel the person is in)
def do_list(screen_name, parts, hashtags, ats):
  pass

# Create a new channel using a random word.
def do_new(screen_name, parts, hashtags, ats):
  if (len(parts) > 1):
    dont_understand(screen_name)
  else:
    new_hashtag = urllib2.urlopen("http://randomword.setgetgo.com/get.php").read()
    cursor.execute("INSERT INTO channels VALUES (%s, %s)",[new_hashtag, screen_name])
    cursor.execute("INSERT INTO users VALUES (%s, %s, %s)",[screen_name, new_hashtag, True])
    db.commit()
    dm(screen_name, "New channel created called #" + new_hastag)

# Attempt to destroy an existing channel. Must be owner. DM all current members to say 'going down'
def do_kill(screen_name, parts, hashtags, ats):
  if (len(hashtags) == 0):
    dont_understand(screen_name)
  else:
    channel = hashtags[0]
    num_rows = cursor.execute("SELECT owner_screen_name FROM channel WHERE channel_hashtag=%s",[channel])
    if (num_rows == 0):
      # No such channel
      dont_understand(screen_name)
    else:
      row = cursor.fetchone()
      if (row[0] != screen_name):
        # The user doesn't own the channel
          dont_understand(screen_name)
      else:
        # Inform all the full members
        broadcast(channel, "@" + screen_name + " has closed channel " + channel)
        # Remove all the invited members
        cursor.execute("SELECT screen_name FROM users WHERE channel=%s AND member=%s",[channel, False])
        for row in cursor.fetchall():
          if (is_follower(row[0])):
            dm(row[0], "@" + screen_name + " has closed channel " + channel)
        # Remove from DB
        cursor.execute("DELETE from users WHERE channel_hashtag=%s",[channel])
        cursor.execute("DELETE from channels WHERE channel_hashtag=%s",[channel])
        db.commit()

# Attempt to add potentially multiple people to an existing channel. Must be owner.
# They musy be followers. DM failure or DM owner to say they've been invited.
def do_add(screen_name, parts, hashtags, ats):
  pass

# Attempt to boot someone off a channel, DM failure back or remove and DM person gone and all left
def do_boot(screen_name, parts, hashtags, ats):
  if (len(hashtags) == 0):
    dont_understand(screen_name)
  else:
    channel = hashtags[0]
    if (len(ats) != 1):
      dont_understand(screen_name)
    else:
      bootee = ats[1:] # Strip '@' off the front
      check_val = is_member(bootee, channel)
      if (check_val is None):
        # Can't boot a non-member
        dont_understand(screen_name)
      else:
        cursor.execute("DELETE FROM users WHERE channel_hashtag=%s AND screen_name=%s",[channel, bootee])
        con.commit()
        if (check_val == False):
          # They were only at the invite stage
          dm(screen_name, "@" + bootee + " has been de-invited from channel " + channel)
          dm(bootee, "You have been de-invited from channel " + channel)
        else:
          # They were a full member
          dm(bootee, "@" + screen_name + " has removed you from channel " + channel)
          broadcast(channel, "@" + screen_name + " has removed @" + bootee + "from channel " + channel)

# Attempt to join an existing channel, check if they have been invited, if successful
# DM all existing member of the list saying they joined and reply to them
def do_join(screen_name, parts, hashtags, ats):
  if (len(hashtags) == 0):
    dont_understand(screen_name)
  else:
    channel = hashtags[0]
    check_val = is_member(screen_name, channel)
    if (check_val is None):
      # They've never even been invited
      dont_understand(screen_name)
    else:
      if (check_val is True):
        dm(screen_name, "You are already a member of channel " + channel)
      else:
        cursor.execute("INSERT INTO users (screen_name, channel_hashtag, member) VALUES (%S, %s, %s)",[screen_name, channel, False])
        con.commit()
        broadcast(channel, "Please welcome " + screen_name + " to channel " + channel)
        
# Attempt to leave an existing channel, check they're a member, DM all current members 
# to say they've left and DM they to say left
def do_leave(screen_name, parts, hashtags, ats):
  if (len(hashtags) == 0):
    dont_understand(screen_name)
  else:
    channel = hashtags[0]
    check_val = is_member(screen_name, channel)
    if (check_val is None):
      # They're not a member of that channel
      dont_understand(screen_name)
    else:
      cursor.execute("DELETE FROM users WHERE channel_hashtag=%s AND screen_name=%s",[channel, screen_name])
      con.commit()
      if (check_val):
        # They were a full member
        dm(screen_name, "You have left channel " + channel)
        broadcast(channel, "@" + screen_name + " has left channel " + channel)
      else:
        # They were a pending member
        dm(screen_name, "Pending request for channel " + channel + " has been removed")
        broadcast(channel, "@" + screen_name + " has declined to join channel " + channel)

# Attempt to broadcast to everyone on the given channel (check it's defined)
def do_broadcast(screen_name, parts, hashtags, ats):
  parts.insert(0, "@" + screen_name)  
  dm_text = " ".join(parts)
  broadcast(hashtags[0], dm_text)

# Function to DM passed-in text to everyone on a channel
def broadcast(channel, text):
  cursor.execute("SELECT screen_name FROM users WHERE channel_hastag=%s AND member=%s",[channel, True])
  for row in cursor.fetchall():
    dm(row[0], text)

# Function to DM passed-in text to supplied user
# Nb handles messages > 140 chars by splitting into chunks
def dm(screen_name, dm_text):
  begin_pos = 0
  end_pos = dm_text.rfind(" ", 0, 140)
  while (end_pos != -1):
    send_text = dm_text[begin_pos:end_pos]
    twitter.direct_messages.new(screen_name = screen_name, text = send_text)
    dm_text = dm_text[end_pos+1:]
    end_pos = dm_text.rfind(" ", 0, 140)
  twitter.direct_messages.new(screen_name = screen_name, text = dm_text)

# Function to check whether a given user is a member of a channel
def is_member(screen_name, channel):
  rows_returned = cursor.execute("SELECT member FROM users WHERE screen_name=%s AND channel_hastag=%s",[screen_name, channel])
  if (rows_returned == 0):
    return None
  else:
    row = cursor.fetchone()
    return row[0]

# Function to check whether a given user follows BackChannel
def is_follower(screen_name):
  result = twitter.friendships.show(source_screen_name = '_BackChannel_', target_screen_name = screen_name)
  return = result["relationship"]["target"]["followed_by"]

# Function to return "don't understand" to a user
def dont_understand(screen_name):
  dm(screen_name, "Sorry, I don't understand, for help see http://stuff.thing")

"""
# NOTES #

Test account : @TestyMcTest99

Database: LIKE %s",[2,digest+"_"+charset+"_%"])
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

"""
