import sqlite3
from datetime import datetime, timedelta, date
import streamlit as st
import webbrowser
import fitbit
from requests_oauthlib import OAuth2Session
import pandas as pd
import os

# --------------------FitBit Access --------------------

def save_fitbit_tokens(email, access_token, refresh_token, expires_in):
    """Saves Fitbit tokens to the database."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    expiry_time = datetime.now() + timedelta(seconds=expires_in)
    cursor.execute('''
        INSERT OR REPLACE INTO fitbit_tokens (email, access_token, refresh_token, token_expiry)
        VALUES (?, ?, ?, ?)
    ''', (email, access_token, refresh_token, expiry_time))
    conn.commit()
    conn.close()

def get_fitbit_tokens(email):
    """Retrieves Fitbit tokens for the given email."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT access_token, refresh_token, token_expiry FROM fitbit_tokens WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'access_token': row[0],
            'refresh_token': row[1],
            'token_expiry': row[2]
        }
    return None

class FitbitDataRetriever:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = 'http://localhost:8080'
        self.authorization_base_url = 'https://www.fitbit.com/oauth2/authorize'
        self.token_url = 'https://api.fitbit.com/oauth2/token'
        self.scope = [
            'activity', 'heartrate', 'location', 
            'nutrition', 'profile', 'settings', 
            'sleep', 'weight'
        ]
        self.oauth = None
        self.token = None

    def authorize(self, email):
        """Handles Fitbit OAuth 2.0 authorization."""
        self.oauth = OAuth2Session(
            self.client_id, 
            scope=self.scope, 
            redirect_uri=self.redirect_uri
        )
        authorization_url, state = self.oauth.authorization_url(
            self.authorization_base_url, 
            access_type='offline'
        )
        st.write("Please go to this URL and authorize:")
        st.write(authorization_url)
        webbrowser.open(authorization_url)
        authorization_response = st.text_input("Enter the full callback URL:")
        if st.button("Submit Authorization Code"):
            self.token = self.oauth.fetch_token(
                self.token_url, 
                authorization_response=authorization_response,
                client_secret=self.client_secret
            )
            save_fitbit_tokens(email, self.token['access_token'], self.token['refresh_token'], self.token['expires_in'])
            st.success("✅ Successfully connected to Fitbit!")
            return self.token

    def get_heart_rate_data(self, email, target_date=None):
        """Fetches heart rate data for the given user."""
        if not target_date:
            target_date = datetime.today().strftime("%Y-%m-%d")

        tokens = get_fitbit_tokens(email)
        if not tokens:
            st.error("No Fitbit account connected for this email.")
            return None

        client = fitbit.Fitbit(
            self.client_id, 
            self.client_secret, 
            oauth2=True, 
            access_token=tokens['access_token'], 
            refresh_token=tokens['refresh_token']
        )

        try:
            hr_data = client.intraday_time_series('activities/heart', base_date=date, detail_level='1min')
            hr_df = pd.DataFrame(hr_data['activities-heart-intraday']['dataset'])
            return hr_df
        except Exception as e:
            st.error(f"Error retrieving heart rate data: {e}")
            return None

    def get_sleep_data(self, email, target_date=None):
        """Fetches sleep data for the given user."""
        if not target_date:
            target_date = datetime.today().strftime("%Y-%m-%d")

        tokens = get_fitbit_tokens(email)
        if not tokens:
            st.error("No Fitbit account connected for this email.")
            return None

        client = fitbit.Fitbit(
            self.client_id, 
            self.client_secret, 
            oauth2=True, 
            access_token=tokens['access_token'], 
            refresh_token=tokens['refresh_token']
        )

        try:
            sleep_data = client.get_sleep(date)
            return sleep_data
        except Exception as e:
            st.error(f"Error retrieving sleep data: {e}")
            return None