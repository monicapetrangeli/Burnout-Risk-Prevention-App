import sqlite3

# -------------------- Burnout Predictions --------------------

def save_burnout_percentage(user_id, risk_percentage):
    """Saves the burnout risk percentage to the database."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO burnout_history (user_id, date, risk_percentage)
        VALUES (?, DATETIME('now'), ?)
    ''', (user_id, risk_percentage))
    conn.commit()
    conn.close()

def get_burnout_history(user_id):
    """Fetches the burnout history for the given user with daily granularity."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DATE(date) AS day, AVG(risk_percentage) AS avg_risk
        FROM burnout_history
        WHERE user_id = ?
        GROUP BY day
        ORDER BY day DESC
        LIMIT 30
    ''', (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data