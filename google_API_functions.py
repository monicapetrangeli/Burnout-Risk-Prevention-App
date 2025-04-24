import sqlite3
import streamlit as st
import pickle
import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# -------------------- Google Calendar Functions --------------------
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Authenticates and returns a Google Calendar API service instance."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('calendar', 'v3', credentials=creds)

def schedule_event(summary, description, duration_minutes):
    """Schedules an event in the user's Google Calendar if 24 hours have passed since the last scheduled task."""
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("User not signed in. Cannot schedule events.")
        return

    # Check the last scheduled task timestamp
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_scheduled FROM scheduled_tasks WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()

    now = datetime.utcnow()
    if row:
        last_scheduled = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        time_since_last = now - last_scheduled
        if time_since_last < timedelta(hours=24):
            st.info("A task has already been scheduled in the last 24 hours. No new task will be scheduled.")
            conn.close()
            return

    # Schedule the event
    service = get_calendar_service()
    start_time = now + timedelta(minutes=5)  # Schedule 5 minutes from now
    end_time = start_time + timedelta(minutes=duration_minutes)
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time.isoformat() + 'Z'},
        'end': {'dateTime': end_time.isoformat() + 'Z'}
    }
    service.events().insert(calendarId='primary', body=event).execute()

    # Update the last scheduled task timestamp
    if row:
        cursor.execute('UPDATE scheduled_tasks SET last_scheduled = ? WHERE user_id = ?', (now.strftime('%Y-%m-%d %H:%M:%S'), user_id))
    else:
        cursor.execute('INSERT INTO scheduled_tasks (user_id, last_scheduled) VALUES (?, ?)', (user_id, now.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

    st.success("Task scheduled successfully!")

def get_weekly_calendar_events():
    """Fetches events from the user's Google Calendar for the next 7 days."""
    service = get_calendar_service()
    now = datetime.utcnow().isoformat() + 'Z'
    one_week_later = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=one_week_later,
        singleEvents=True,
        orderBy='startTime',
        timeZone='Europe/Madrid',
        fields='items(id,start,end,summary)'
    ).execute()


    events = events_result.get('items', [])
    formatted_events = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        summary = event.get('summary', 'No Title')
        event_id = event.get('id') 
        formatted_events.append({
            'start': start,
            'end': end,
            'summary': summary,
            'id': event_id              
        })

    return formatted_events

# -------------------- Schecule Custom Task --------------------
def schedule_custom_task(summary, description, start_datetime, duration_minutes=60):
    service = get_calendar_service()

    end_datetime = start_datetime + timedelta(minutes=duration_minutes)

    # Quitar tzinfo para que Google use correctamente 'timeZone'
    start_str = start_datetime.replace(tzinfo=None).isoformat()
    end_str = end_datetime.replace(tzinfo=None).isoformat()

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_str,
            'timeZone': 'Europe/Madrid'
        },
        'end': {
            'dateTime': end_str,
            'timeZone': 'Europe/Madrid'
        }
    }

    service.events().insert(calendarId='primary', body=event).execute()