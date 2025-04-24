import sqlite3

# -------------------- User Profile --------------------

def save_user_profile(dob, gender, family_size, num_pets, city, education, job, remote_percentage,name):
    """Saves the user profile to the database."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_profile')
    cursor.execute('''
        INSERT INTO user_profile (dob, gender, family_size, num_pets, city, education, job, remote_percentage, name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (dob, gender, family_size, num_pets, city, education, remote_percentage, job, name))
    conn.commit()
    conn.close()

def load_user_profile():
    """Loads the user profile from the database."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_profile LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'dob': row[1],
            'gender': row[2],
            'family_size': row[3],
            'num_pets': row[4],
            'city': row[5],
            'education': row[6],
            'remote_percentage': row[7],
            'job':row[8],
            'name':row[9],
        }
    return None