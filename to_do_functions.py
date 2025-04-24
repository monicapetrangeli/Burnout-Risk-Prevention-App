import sqlite3

# -------------------- To-Do List --------------------

def save_todo(user_id, task):
    """Saves a new task to the to-do list for the given user."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO todo_list (user_id, task, completed) VALUES (?, ?, ?)', (user_id, task, False))
    conn.commit()
    conn.close()

def get_todo_list(user_id):
    """Fetches the to-do list for the given user."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, task, completed FROM todo_list WHERE user_id = ?', (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def update_todo_status(user_id, task_id, completed):
    """Updates the status of a task in the to-do list for the given user."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE todo_list SET completed = ? WHERE id = ? AND user_id = ?', (completed, task_id, user_id))
    conn.commit()
    conn.close()

def delete_todo(user_id, task_id):
    """Deletes a task from the to-do list for the given user."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM todo_list WHERE id = ? AND user_id = ?', (task_id, user_id))
    conn.commit()
    conn.close()
