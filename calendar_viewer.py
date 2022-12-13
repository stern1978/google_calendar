#!/usr/bin/python3

from __future__ import print_function
import httplib2
import os

import googleapiclient.discovery as discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from datetime import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None




SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret_google_calendar.json'
APPLICATION_NAME = 'Google Calendar - Raw Python'
import datetime
from flask import Flask, render_template


app = Flask(__name__)
app.config.from_object(__name__)


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'calendar-python-quickstart.json')
 
    store = Storage(credential_path)
    credentials = store.get()

    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        #print('Storing credentials to ' + credential_path)
    return credentials


 
@app.route('/')
def index():
    calendar = []
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    page_token = None
    calendar_ids = []
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            if '@gmail.com' in calendar_list_entry['id']:
                calendar_ids.append(calendar_list_entry['id'])
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break
    
    end_date = datetime.datetime.utcnow().isoformat() + 'Z'
    today_iso = datetime.datetime.now()
    today = today_iso.strftime('%b %d')
    tomorrow_iso = today_iso + datetime.timedelta(days=1)
    tomorrow = tomorrow_iso.strftime('%b %d')
    week_iso = today_iso + datetime.timedelta(days=6)
    week = week_iso.strftime('%a')
    

    for calendar_id in calendar_ids:
        eventsResult = service.events().list(
            calendarId=calendar_id,
            singleEvents=True,
            timeMin = end_date,
            maxResults = 10,
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])
        for event in events:
            summary = event['summary']
            try:
                location = event['location']
            except KeyError:
                location = ''
            try:
                start_iso = event['start']['dateTime']
                start_iso_slice = datetime.datetime.strptime(start_iso[slice(-6)], '%Y-%m-%dT%H:%M:%S')
                start_time = datetime.datetime.strptime(start_iso, '%Y-%m-%dT%H:%M:%S%z').strftime('%I:%M %p')
                start_date = datetime.datetime.strptime(start_iso, '%Y-%m-%dT%H:%M:%S%z').strftime('%b %d')
                start_day = datetime.datetime.strptime(start_iso, '%Y-%m-%dT%H:%M:%S%z').strftime('%a')
            except KeyError:
                start_iso = event['start']['date']
                start_iso_string = datetime.datetime.strptime(start_iso, '%Y-%m-%d').strftime('%Y-%m-%dT%H:%M:%S')
                start_iso_slice = datetime.datetime.strptime(start_iso_string, '%Y-%m-%dT%H:%M:%S')
                start_time = 'All Day'
                start_date = datetime.datetime.strptime(start_iso, '%Y-%m-%d').strftime('%b %d')
                start_day = datetime.datetime.strptime(start_iso, '%Y-%m-%d').strftime('%a')
            if today > week:
                start_date
            elif today == start_date:
                start_date = 'Today'
            elif tomorrow == start_date:
                start_date = 'Tomorrow'
            elif week_iso > start_iso_slice:
                start_date = start_day
                
            calendar.append([summary, location, start_time, start_date, today])
    return render_template('calendar.html',calendar=calendar)


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8014, debug=True)