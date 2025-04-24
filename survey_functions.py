import sqlite3
from datetime import datetime
import os

# -------------------- Daily Survey --------------------

def has_submitted_survey_today(user_id):
    """Checks if the user has submitted the daily stress survey today."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_submission FROM daily_stress_submissions WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        try:
            # Try parsing with fractional seconds
            last_submission = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            # Fallback to parsing without fractional seconds
            last_submission = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        return last_submission.date() == datetime.now().date()
    return False

def update_survey_submission_timestamp(user_id):
    """Updates the last submission timestamp for the daily stress survey."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO daily_stress_submissions (user_id, last_submission)
        VALUES (?, ?)
    ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')))
    conn.commit()
    conn.close()

def load_recent_survey_data(user_id):
    """Loads the most recent survey data for the given user."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT mood, stress_level, work_hours, weekend_overtime, exercise_hours, sleep_hours
        FROM daily_stress_submissions
        WHERE user_id = ?
        ORDER BY last_submission DESC
        LIMIT 1
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        # Ensure all fields have default values if they are None
        return {
            'mood': row[0] if row[0] is not None else 'Happy',  # Default to 5
            'stress_level': row[1] if row[1] is not None else 5,  # Default to 5
            'work_hours': row[2] if row[2] is not None else 8.0,  # Default to 8.0
            'weekend_overtime': row[3] if row[3] is not None else 0.0,  # Default to 0.0
            'exercise_hours': row[4] if row[4] is not None else 1.0,  # Default to 1.0
            'sleep_hours': row[5] if row[5] is not None else 7.0  # Default to 7.0
        }
    return None