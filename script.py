import requests
import json
import os
from flask import Flask
import time
import subprocess

app = Flask(__name__)

AA_NETWORK_KEY = os.environ['AA_NETWORK_KEY']
AA_USERNAME = os.environ['AA_USERNAME']
AA_PASSWORD = os.environ['AA_PASSWORD']
AUDIO_PLAYER = os.environ['AUDIO_PLAYER']

now_playing = {"channel":"test", "expires":0}


member_session = requests.post(f"https://api.audioaddict.com/v1/{AA_NETWORK_KEY}/member_sessions", data={"member_session[username]":AA_USERNAME, "member_session[password]":AA_PASSWORD}, auth=requests.auth.HTTPBasicAuth('streams', 'diradio'))

member_session = json.loads(member_session.text)

TOKEN = member_session['key']
print(TOKEN)




channel_resp = requests.get(f"https://api.audioaddict.com/v1/{AA_NETWORK_KEY}/channels", headers={'X-Session-Key': TOKEN})
channels = json.loads(channel_resp.text)
CHANNELS = {}
for channel in channels:
    data = {}
    data['id'] = channel['id']
    data['name'] = channel['name']
    data['premium_id'] = channel['premium_id']
    CHANNELS[channel['key']] = data

def get_track_history(channel):
    channel_id = CHANNELS[channel]['id']
    print("Channel ID:", channel_id)
    track_history = requests.get(f"https://api.audioaddict.com/v1/{AA_NETWORK_KEY}/track_history/channel/{channel_id}")
    track_history = json.loads(track_history.text)
    return track_history

def get_most_recent_track(channel):
    return get_track_history(channel)[0]

def vote(track_id, direction, channel = None):
    if channel is not None:
        channel = str(CHANNELS[channel]['id']) + "/"
    request_url = f"https://api.audioaddict.com/v1/{AA_NETWORK_KEY}/tracks/{track_id}/vote/{channel}{direction}/"
    response = requests.post(request_url, headers={'X-Session-Key': TOKEN})
    
def vote_current_track(channel, direction):
    track = get_most_recent_track(channel)
    vote(track['track_id'], direction, channel)

def get_channel():
    channel = subprocess.run([f"./{AUDIO_PLAYER}/get_channel.sh"], stdout = subprocess.PIPE)
    channel = channel.stdout.decode('utf-8').strip()
    return channel

def update_now_playing(channel):
    track = get_most_recent_track(channel)
    expires = int(track['started']) + int(track['duration'])
    global now_playing
    now_playing = {"channel": channel, "expires": expires, "track": track, "vote": "X"}
    print("Updating track...")

@app.route("/nowplaying/")
def nowplaying():
    channel = get_channel()
    if now_playing['channel'] != channel:
        update_now_playing(channel)
        print("Updated because of channel update")
    if now_playing['expires'] < time.time():
        update_now_playing(channel)
        print("Updated because of expiration")
    return "Ch: %s :: %s - %s :: Vt %s" % (CHANNELS[channel]['name'], now_playing['track']['display_artist'], now_playing['track']['display_title'], now_playing['vote'])

@app.route("/vote/<direction>")
def vote_url(direction):
    global now_playing
    now_playing['vote'] = direction
    channel = get_channel()
    vote_current_track(channel, direction)
    return "OK!"
