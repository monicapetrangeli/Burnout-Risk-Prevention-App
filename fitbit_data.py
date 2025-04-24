import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

import fitbit
import datetime
import pandas as pd
from requests_oauthlib import OAuth2Session
import webbrowser
import requests

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

    def authorize(self):
        self.oauth = OAuth2Session(
            self.client_id, 
            scope=self.scope, 
            redirect_uri=self.redirect_uri
        )
        authorization_url, state = self.oauth.authorization_url(
            self.authorization_base_url, 
            access_type='offline'
        )
        print("Please go to this URL and authorize:")
        print(authorization_url)
        webbrowser.open(authorization_url)
        authorization_response = input("Enter the full callback URL: ")
        self.token = self.oauth.fetch_token(
            self.token_url, 
            authorization_response=authorization_response,
            client_secret=self.client_secret
        )
        print("✅ Successfully connected to Fitbit!")
        return self.token

    def get_heart_rate_data(self, date=None):
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")

        client = fitbit.Fitbit(
            self.client_id, 
            self.client_secret, 
            oauth2=True, 
            access_token=self.token['access_token'], 
            refresh_token=self.token['refresh_token']
        )

        try:
            hr_data = client.intraday_time_series('activities/heart', base_date=date, detail_level='1min')
            hr_df = pd.DataFrame(hr_data['activities-heart-intraday']['dataset'])
            return hr_df
        except Exception as e:
            print(f"Error retrieving heart rate data: {e}")
            return None

    def get_sleep_data(self, date=None):
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")

        client = fitbit.Fitbit(
            self.client_id, 
            self.client_secret, 
            oauth2=True, 
            access_token=self.token['access_token'], 
            refresh_token=self.token['refresh_token']
        )

        try:
            sleep_data = client.get_sleep(date)
            return sleep_data
        except Exception as e:
            print(f"Error retrieving sleep data: {e}")
            return None

def main():
    CLIENT_ID = 'add your client id here'
    CLIENT_SECRET = 'add your client secret here'

    fitbit_retriever = FitbitDataRetriever(CLIENT_ID, CLIENT_SECRET)
    token = fitbit_retriever.authorize()

    heart_rate_df = fitbit_retriever.get_heart_rate_data()
    if heart_rate_df is not None and not heart_rate_df.empty:
        print("Heart Rate Data:")
        print(heart_rate_df.head())
    else:
        print("No heart rate data available.")

    sleep_data = fitbit_retriever.get_sleep_data()
    if sleep_data is not None:
        print("\nSleep Data:")
        print(sleep_data)
    else:
        print("No sleep data available.")

    # --- SIMULATED DATA FROM FITBIT FILES ---
    print("\n--- Using simulated Fitbit data ---")

    activity = pd.read_csv("/Users/carlotatejeda/Desktop/MSc/Term 2/Prototyping/Final project/fitbit/dailyActivity_merged1.csv")
    sleep = pd.read_csv("/Users/carlotatejeda/Desktop/MSc/Term 2/Prototyping/Final project/fitbit/sleepDay_merged.csv")
    weight = pd.read_csv("/Users/carlotatejeda/Desktop/MSc/Term 2/Prototyping/Final project/fitbit/weightLogInfo_merged.csv")

    activity['ActivityDate'] = pd.to_datetime(activity['ActivityDate'])
    sleep['SleepDay'] = pd.to_datetime(sleep['SleepDay'])
    weight['Date'] = pd.to_datetime(weight['Date'])

    df = pd.merge(activity, sleep, left_on='ActivityDate', right_on='SleepDay', how='left')
    df = pd.merge(df, weight, left_on='ActivityDate', right_on='Date', how='left')

    df = df[['ActivityDate', 'TotalSteps', 'TotalDistance', 'Calories', 'TotalMinutesAsleep', 'WeightKg']]
    df = df.dropna(subset=['TotalSteps', 'TotalMinutesAsleep'])

    df['burnout_risk'] = (df['TotalSteps'] < 4000) & (df['TotalMinutesAsleep'] < 300)

    print("\n--- Simulated Fitbit Data ---")
    print(df.head())

    print("\n--- Burnout Prediction ---")
    print(df[['ActivityDate', 'TotalSteps', 'TotalMinutesAsleep', 'burnout_risk']].head())

if __name__ == "__main__":
    main()
