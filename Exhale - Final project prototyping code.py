import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from datetime import timedelta, date, time, datetime
import sqlite3
import plotly.express as px
import hashlib
from urllib.parse import urlencode
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import altair as alt
from fitbit_data import FitbitDataRetriever
from pytz import timezone
import pytz
import random 
from survey_functions import has_submitted_survey_today, update_survey_submission_timestamp, load_recent_survey_data
from fitbit_functions import save_fitbit_tokens, get_fitbit_tokens
from google_API_functions import get_calendar_service, schedule_event, schedule_custom_task, get_weekly_calendar_events
from to_do_functions import save_todo, get_todo_list, update_todo_status, delete_todo
from burnout_predictions_functions import save_burnout_percentage, get_burnout_history
from database_functions import create_database, update_database_schema
from user_profile_functions import save_user_profile, load_user_profile

# -------------------- Model Definition --------------------

def predict_burnout_risk(age, gender, work_hours=8.0, sleep_hours=7.0, weekend_overtime=0.0,
                         stress_level=5, job_avg_stress=5, education=1, city='Small',
                         family_size=0, num_pets=0, exercise_hours=1.0, remote_percentage=0.5):
    
    score = 0
    # Age: older age reduces burnout risk
    score += -0.2 * age  
    # Gender: female workers have a higher risk
    score += 0.7 if gender.lower() == 'female' else 0

    # Work hours: baseline for first 8 hours and extra for overtime
    baseline_hours = 8
    score += 0.3 * min(work_hours, baseline_hours)
    score += 0.5 * max(0, work_hours - baseline_hours)

    # Sleep: more sleep reduces risk
    score += -0.4 * sleep_hours
    # Overtime: increased weekend overtime increases risk
    score += 0.6 * weekend_overtime

    # Stress factors: higher stress strongly increases burnout risk
    score += 1.0 * stress_level
    score += 0.8 * job_avg_stress

    # Education: higher education increases risk
    score += 0.2 * education
    # City: living in a big city adds a modest risk
    score += 0.3 if city.lower() == 'big' else 0

    # Family size: larger family responsibilities might increase risk
    score += 0.1 * family_size
    # Pets: presence of pets might help reduce stress
    score += -0.2 * num_pets
    # Exercise: more exercise reduces burnout risk
    score += -0.3 * exercise_hours
    # Remote work: higher remote percentage might increase risk (but effect is moderated)
    score += 0.4 * remote_percentage

    # Daily steps: more steps are linked with lower burnout risk
    # Here, we subtract 0.0002 per step (i.e., ~2 points reduction for 10,000 steps)
#    score += -0.0002 * daily_steps
    # ------------------------------
    # Scale score to percentage (0-100%)
    # ------------------------------
    MIN_SCORE = -10  
    MAX_SCORE = 20  
    risk_percentage = (score - MIN_SCORE) / (MAX_SCORE - MIN_SCORE) * 100
    risk_percentage = max(0, min(100, risk_percentage)) 

    return risk_percentage, score

# -------------------- Job Stress Dictionary --------------------

job_stress_levels = {
    "Air Traffic Controller": 9,
    "Surgeon": 9,
    "Firefighter": 8,
    "Commercial Airline Pilot": 8,
    "Police Officer": 8,
    "Corporate Executive": 7,
    "Journalist": 7,
    "Emergency Medical Technician (EMT)": 7,
    "Stockbroker": 7,
    "Event Coordinator": 6,
    "Teacher": 6,
    "Nurse": 6,
    "IT Manager": 6,
    "Sales Manager": 6,
    "Social Worker": 6,
    "Engineer": 5,
    "Accountant": 5,
    "Architect": 5,
    "Electrician": 5,
    "Customer Service Representative": 5,
    "Administrative Assistant": 4,
    "Graphic Designer": 4,
    "Librarian": 3,
    "Data Entry Clerk": 3,
    "Translator": 3,
    "Receptionist": 3,
    "Florist": 2,
    "Tailor": 2,
    "Student": 7,
    "Stay-at-Home Parent": 7
}

# -------------------- Age Calculation Function --------------------
def calculate_age(dob):
        """Calculates the age based on the date of birth."""
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

# -------------------- Streamlit Pages --------------------
def hash_password(password):
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

    # -------------------- Sign in Page --------------------
def sign_in():
    """Handles user sign-in with a modern and calming design."""
    # Custom CSS for styling
    st.markdown("""
    <style>

    /* Title styling */
    .title {
        font-size: 48px;
        font-weight: bold;
        color: #a3c9a8;
        margin-bottom: 10px;
    }

    /* Subtitle styling */
    .subtitle {
        font-size: 20px;
        font-style: italic;
        color: #457b9d;
        margin-bottom: 20px;
    }

    /* Button styling */
    .stButton>button {
        background-color: #b392ac !important;
        color: white !important;
        border-radius: 40px !important;
        font-size: 18px;
        font-weight: bold;
        padding: 10px 20px;
        border: none;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.15);
    }

    /* Image styling */
    .sign-in-image {
        margin-bottom: 0px; /* Reduced space below the image */
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        # Display the image on the left
        st.image("sign_in.webp", caption="", use_container_width=True)

    with col2:
        # Display the title and subtitle on the right
        st.markdown('<div class="title">EXHALE</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Breath out stress, Breath in balance</div>', unsafe_allow_html=True)

        # Sign-in logic
    email = st.text_input("Email", placeholder="user@example.com")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    if st.button("Let's start"):
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_id, hashed_password = user
            if hash_password(password) == hashed_password:
                st.session_state['user_id'] = user_id
                st.session_state['email'] = email
                if has_submitted_survey_today(user_id):
                    st.session_state['page'] = 'main'
                else:
                    st.session_state['page'] = 'daily_stress_survey'
                st.success("✅ Sign-in successful! Redirecting...")
            else:
                st.error("❌ Incorrect password. Please try again.")
        else:
            st.warning("⚠️ Email not found. Redirecting to create account...")
            st.session_state['email'] = email
            st.session_state['page'] = 'create_account'

# -------------------- Create Account Page --------------------

def create_account():
    """Handles account creation for new users."""

    # Custom CSS for styling (same as Sign In page)
    st.markdown("""
    <style>

    /* Title styling */
    .title {
        font-size: 48px;
        font-weight: bold;
        color: #a3c9a8;
        margin-bottom: 10px;
    }

    /* Subtitle styling */
    .subtitle {
        font-size: 20px;
        font-style: italic;
        color: #457b9d;
        margin-bottom: 20px;
    }

    /* Button styling */
    .stButton>button {
        background-color: #b392ac !important;
        color: white !important;
        border-radius: 40px !important;
        font-size: 18px;
        font-weight: bold;
        padding: 10px 20px;
        border: none;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.15);
    }

    /* Image styling */
    .sign-in-image {
        margin-bottom: 0px; /* Reduced space below the image */
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout with two columns (image on the left, form on the right)
    col1, col2 = st.columns([1, 2])
    with col1:
        # Display the image on the left
        st.image("sign_in.webp", caption="", use_container_width=True)

    with col2:
        # Display the title and subtitle on the right
        st.markdown('<div class="title">EXHALE</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Breath out stress, Breath in balance</div>', unsafe_allow_html=True)

        # Account creation form
        email = st.text_input("Email", value=st.session_state.get('email', ''), placeholder="user@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")

        if st.button("Create Account"):
            if password != confirm_password:
                st.error("Passwords do not match. Please try again.")
                return

            hashed_password = hash_password(password)

            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
                conn.commit()
                user_id = cursor.lastrowid
                st.session_state['user_id'] = user_id
                st.session_state['page'] = 'onboarding'
                st.success("Account created successfully! Redirecting to onboarding...")
            except sqlite3.IntegrityError:
                st.error("An account with this email already exists. Please sign in.")
            finally:
                conn.close()

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Onboarding page --------------------

def onboarding():
    """Handles the onboarding process for new users."""
    # Custom CSS for styling
    st.markdown("""
    <style>
    .onboarding-title {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        color: #a3c9a8;
        margin-bottom: 10px;
    }
    .onboarding-subtitle {
        text-align: center;
        font-size: 20px;
        font-style: italic;
        color: #457b9d;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #b392ac !important;
        color: white !important;
        border-radius: 40px !important;
        font-size: 18px;
        font-weight: bold;
        padding: 10px 20px;
        border: none;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.15);
    }
    </style>
    """, unsafe_allow_html=True)

    # Centered container for the onboarding form
    st.markdown('<div class="onboarding-title">Welcome to Exhale</div>', unsafe_allow_html=True)
    st.markdown('<div class="onboarding-subtitle">Tell us a bit about yourself</div>', unsafe_allow_html=True)

    # Check login
    user_id = st.session_state.get('user_id')
    email = st.session_state.get('email')
    if not user_id:
        st.error("User not signed in. Redirecting to sign-in...")
        st.session_state['page'] = 'sign_in'
        return

    # Avoid duplicate onboarding
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_profile WHERE user_id = ?', (user_id,))
    profile = cursor.fetchone()
    conn.close()

    if profile:
        st.info("Profile already exists. Redirecting to the main page...")
        st.session_state['page'] = 'main'
        return

    # Collect user info
    name = st.text_input('How should I call you?')
    dob = st.date_input('Date of Birth', min_value=date(1900, 1, 1), max_value=date.today(), value=date(1990, 1, 1))
    gender = st.selectbox('Gender', ['Male', 'Female'])
    family_size = st.number_input('Family Size', min_value=0, value=2)
    num_pets = st.number_input('Number of Pets', min_value=0, value=1)
    city = st.selectbox('City Size', ['Small', 'Big'])
    education = st.selectbox('Education Level', ['High School', 'Bachelor', 'Master', 'PhD'])
    remote_percentage = st.slider('Remote Work Percentage', 0.0, 1.0, 0.5)
    job = st.selectbox('Job', list(job_stress_levels.keys()))

    fitbit_retriever = FitbitDataRetriever('23Q56Z', '1ed3890271875514537ca3067417a496')
    if st.button("Connect Fitbit"):
        fitbit_retriever.authorize()

    # Save profile
    if st.button("Save Profile"):
        education_map = {'High School': 1, 'Bachelor': 2, 'Master': 3, 'PhD': 4}
        education_numeric = education_map[education]

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_profile (user_id, name, dob, gender, family_size, num_pets, city, education, remote_percentage, job)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, dob, gender, family_size, num_pets, city, education_numeric, remote_percentage, job))
        conn.commit()
        conn.close()

        st.success("✅ Profile saved! Redirecting to the daily stress survey...")
        st.session_state['page'] = 'daily_stress_survey'

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Daily Stress Survey --------------------

def daily_stress_survey():
    """Handles the daily stress survey for the user."""

    # Custom CSS for styling
    st.markdown("""
    <style>
    /* Title styling */
    .title {
        font-size: 36px;
        font-weight: bold;
        color: #a3c9a8;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Subtitle styling */
    .subtitle {
        font-size: 18px;
        font-style: italic;
        color: #457b9d;
        text-align: center;
        margin-bottom: 30px;
    }

    /* Button styling */
    .stButton>button {
        background-color: #b392ac !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        padding: 10px;
        margin-top: 20px;
    }

    .stButton>button:hover {
        background-color: #d8bfd8 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Title and subtitle
    st.markdown('<div class="title">DAILY STRESS SURVEY</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Tell me, how are you today?</div>', unsafe_allow_html=True)

    # Check if the user is signed in
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("User not signed in. Redirecting to sign-in...")
        st.session_state['page'] = 'sign_in'
        return

    # Check if the user has already submitted the survey today
    if has_submitted_survey_today(user_id):
        st.info("You have already submitted the survey today. Redirecting to the main page...")
        st.session_state['page'] = 'main'
        return

    # Survey questions
    mood_options = {
        "😊": "Happy",
        "😢": "Sad",
        "😡": "Angry",
        "😰": "Anxious",
        "😴": "Tired",
        "😎": "Relaxed"
    }
    selected_mood = st.radio(
        "How are you feeling today?",
        options=list(mood_options.keys()),
        format_func=lambda emoji: f"{emoji} {mood_options[emoji]}",
        horizontal=True,
    )
    stress_level = st.slider("How stressed are you? (1 = Not Stressed, 10 = Extremely Stressed)", 1, 10, 5)
    work_hours = st.slider("How many hours did you work today?", 0.0, 16.0, 8.0)
    weekend_overtime = st.slider("How many hours of overtime did you work this weekend?", 0.0, 16.0, 0.0)
    exercise_hours = st.slider("How many hours did you exercise today?", 0.0, 5.0, 1.0)
    sleep_hours = st.slider("How many hours did you sleep last night?", 0.0, 12.0, 7.0)

    # Submit button
    if st.button("Submit Survey"):
        # Save the survey data to the database
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO daily_stress_submissions (user_id, last_submission, mood, stress_level, work_hours, weekend_overtime, exercise_hours, sleep_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), selected_mood, stress_level, work_hours, weekend_overtime, exercise_hours, sleep_hours))
        conn.commit()
        conn.close()

        st.success("Thank you for submitting the survey! Redirecting to the main page...")
        st.session_state['page'] = 'main'

# -------------------- Main page --------------------

def main_page():
    st.markdown("""
        <style>
        .dashboard-card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.3s ease;
        }
        .dashboard-card:hover {
            transform: scale(1.02);
        }

        /* Tabs container */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab"] {
            background-color: #f1f5f9; /* Default tab background */
            border-radius: 8px;
            padding: 10px 15px;
            transition: all 0.3s ease;
        }

        /* Hover effect for tabs */
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #e2e8f0; /* Slightly darker on hover */
        }

        /* Selected tab styling */
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #A8DADC; /* Light blue from the palette */
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    user_id = st.session_state.get('user_id')
    email = st.session_state.get('email')

    if not user_id:
        st.error("User not signed in. Redirecting to sign-in...")
        st.session_state['page'] = 'sign_in'
        return

    survey_data = load_recent_survey_data(user_id)
    if not survey_data:
        st.error("Survey data not found. Redirecting to daily stress survey...")
        st.session_state['page'] = 'daily_stress_survey'
        return

    # Load user profile
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_profile WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        st.error("User profile not found. Redirecting to onboarding...")
        st.session_state['page'] = 'onboarding'
        return

    dob = datetime.strptime(user[1], '%Y-%m-%d').date()
    gender = user[2]
    family_size = user[3]
    num_pets = user[4]
    city = user[5]
    education = user[6]
    remote_percentage = user[7]
    job = user[8]
    age = calculate_age(dob)
    job_avg_stress = job_stress_levels.get(job, 5)
    name=user[9]

    tab1, tab2 = st.tabs(["Home", "Journal"])

    # --- TAB 1: Home ---
    with tab1:
        st.markdown(f"""<h1 style="font-size: 48px; font-weight: bold; color: #a3c9a8; text-align: left;">Welcome Back {name}</h1>""", unsafe_allow_html=True)

        risk_percentage, risk_factors = predict_burnout_risk(
        age, gender, survey_data['work_hours'], survey_data['sleep_hours'],
        survey_data['weekend_overtime'], survey_data['stress_level'],
        job_avg_stress, education, city, family_size, num_pets,
        survey_data['exercise_hours'], remote_percentage
        )
        save_burnout_percentage(user_id, risk_percentage)

        # Now use risk_percentage
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_percentage,
            title={'text': "<b><i>Your Current Burnout Risk</i></b>", 'font': {'size': 20, 'color': '#457b9d'}, 'align':'left'},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
                'bar': {'color': 'white'},
                'steps': [
                    {'range': [0, 30], 'color': "#A3C9A8"},
                    {'range': [30, 80], 'color': "#A8DADC"},
                    {'range': [80, 100], 'color': "#D8BFD8"}
                ],
                'threshold': {
                    'line': {'color': "lightgray", 'width': 3},
                    'thickness': 0.5,
                    'value': risk_percentage
                }
            }
        ))
        # Display the gauge chart in Streamlit
        st.markdown("<div style='margin-top: -20px;'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        #Wellness Recommendations
        from datetime import date

        st.markdown("<h3 style='font-size: 20px; color: #457B9D; text-align: left;'><b><i>Wellness Recommendations</i></b></h3>", unsafe_allow_html=True)
        # Define tasks based on risk levels and categories
        tasks = {
            "Low Risk": {
                "Mentally Clearing": ("5-Minute Mindful Breathing", 5),
                "Physical Reset": ("Light Stretch or Walk", 10),
                "Emotionally Uplifting": ("Gratitude Journal", 5),
                "Energy-Restoring": ("Hydration Check", 5),
            },
            "Moderate Risk": {
                "Mentally Clearing": ("Guided Meditation or Visualization", 15),
                "Physical Reset": ("Nature Break", 30),
                "Emotionally Uplifting": ("Reflective Journaling Prompt", 10),
            },
            "High Risk": {
                "Energy-Restoring": ("Deep Rest (Nap or Yoga Nidra)", 45),
                "Emotionally Uplifting": ("Talk to Manager / Therapist / Friend", 30),
                "Mentally Clearing": ("Unplug & Do Nothing", 60),
            },
        }

        # Determine risk level
        if risk_percentage >70:
            risk_level = "High Risk"
        elif risk_percentage > 30:
            risk_level = "Moderate Risk"  
        else:
            risk_level = "Low Risk"

        # Display risk level
        st.markdown(f"<p style='color: #b392ac;'><b>Risk Level:</b> {risk_level}</p>", unsafe_allow_html=True)

        # Allow the user to select a category
        categories = list(tasks[risk_level].keys())
        selected_category = st.selectbox("Choose a category:", categories)

        # Display the task for the selected category
        task_name, duration = tasks[risk_level][selected_category]
        st.markdown(f"<p style='color: #b392ac;'><b>Task:</b> {task_name} ({duration} mins)</p>", unsafe_allow_html=True)

        # Allow the user to select a date
        recommendation_date = st.date_input("Select the date to carve some time for you", value=date.today())

        # Schedule the selected task
        if st.button("Schedule Task"):
            start_time = datetime.combine(recommendation_date, time(hour=9))  # Default start time at 9 AM
            europe_madrid = pytz.timezone("Europe/Madrid")
            start_time = europe_madrid.localize(start_time)
            schedule_custom_task(task_name, f"{task_name} - {selected_category}", start_time, duration)
            st.success(f"We scheduled a {task_name} on {recommendation_date} for you")

        #Adding space
        st.markdown("<br>", unsafe_allow_html=True)

        # Burnout Risk History Line Chart
        history = get_burnout_history(user_id)
        if history:
            # Add a styled title for "Your Burnout History"
            st.markdown("""
            <div style="
                background: #457B9D;
                border-radius: 10px;
                margin-bottom: 20px;
                padding: 10px;
            ">
                <h3 style="color: white; text-align: center;">Your Burnout History</h3>
            </div>
            """, unsafe_allow_html=True)

            # Extract dates and percentages from the history
            dates = [row[0] for row in history]
            percentages = [row[1] for row in history]

            # Format dates to exclude time and ensure uniqueness
            unique_dates = list(dict.fromkeys(dates)) 
            unique_percentages = [percentages[dates.index(d)] for d in unique_dates]  

            # Create a line chart using Plotly
            fig = px.line(
                x=unique_dates[::-1], 
                y=unique_percentages[::-1],
                labels={'x': 'Date', 'y': 'Burnout Risk (%)'},
                title=None  # Remove the default title
            )
            fig.update_traces(mode='lines+markers', line=dict(color='#d8bfd8'))
            fig.update_layout(
                xaxis=dict(
                    title=None,
                    showgrid=True,
                    zeroline=True,
                    zerolinecolor='darkgray',
                    zerolinewidth=1,
                    tickformat='%Y-%m-%d',  
                    tickangle=45
                ),
                yaxis=dict(
                    title='Burnout Risk (%)',
                    showgrid=True,
                    zeroline=True,
                    zerolinecolor='darkgray',
                    zerolinewidth=1
                ),
                plot_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No burnout history available. Complete the daily stress survey to start tracking.")


        col1, col_space, col2 =st.columns([2,1,2])

        with col1:
            st.markdown('#')
            # To-Do List
            st.markdown("""
            <div style="
                background: #b392ac;
                border-radius: 10px;
                margin-bottom: 20px;
            ">
                <h3 style="color: white; text-align: center;">To-Do List</h3>
            """, unsafe_allow_html=True)

            tasks = get_todo_list(user_id)
            if tasks:
                for task_id, task_text, completed in tasks:
                    task_col1, task_col2 = st.columns([0.8, 0.2])
                    with task_col1:
                        # Checkbox for marking tasks as completed
                        checked = st.checkbox(task_text, value=completed, key=f"task_{task_id}")
                        if checked != completed:
                            update_todo_status(user_id, task_id, checked)
                            st.rerun()
                    with task_col2:
                        # Green Delete Button
                        delete_button_style = """
                        <style>
                        .stButton > button {
                            background-color: #a3c9a8;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            padding: 5px 10px;
                            font-size: 14px;
                            cursor: pointer;
                        }
                        .stButton > button:hover {
                            background-color: #91b89a;
                        }
                        </style>
                        """
                        st.markdown(delete_button_style, unsafe_allow_html=True)
                        if st.button("✖", key=f"delete_{task_id}"):
                            delete_todo(user_id, task_id)
                            st.rerun()
            else:
                st.markdown("<p style='color: white; text-align: center;'>No tasks available. Add a new task below!</p>", unsafe_allow_html=True)

            # Add New Task Section
            new_task = st.text_input(" ", placeholder="Add a new task...")
            add_task_button = st.button("Add Task", key="add_task_button")
            if add_task_button and new_task.strip():
                save_todo(user_id, new_task.strip())
                st.rerun()


            # Close the To-Do List Box
            st.markdown("</div>", unsafe_allow_html=True)

        with col_space:
            st.markdown("<div style='height: 100%;'></div>", unsafe_allow_html=True)

        #Pie Chart
        with col2:
            total_hours = 24 * 7
            free_time = total_hours - (
                survey_data['work_hours'] * 7 + survey_data['sleep_hours'] * 7 + survey_data['exercise_hours'] * 7)
            time_data = {
                'Work': survey_data['work_hours'] * 7,
                'Sleep': survey_data['sleep_hours'] * 7,
                'Exercise': survey_data['exercise_hours'] * 7,
                'Free Time': free_time
            }
            fig = px.pie(values=list(time_data.values()), 
                         names=list(time_data.keys()),
                         color_discrete_sequence=["#A3C9A8", "#B392AC", "#457B9D", "#D8BFD8"])
            fig.update_traces(textposition='inside', textinfo='percent+label',insidetextfont=dict(color='white'))
            fig.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2, 
                    xanchor="center", 
                    x=0.5 
                )
            )
            st.plotly_chart(fig, use_container_width=True)
    
            st.markdown('</div>', unsafe_allow_html=True)
        
        #Adding space
        st.markdown("<br>", unsafe_allow_html=True)

        #Calendar
        color_palette = ["#A3C9A8", "#A8DADC", "#457B9D", "#D8BFD8", "#B392AC"]
        st.markdown("""
                <div class="dashboard-card" style="padding: 10px 20px; background-color: #457B9D;">
                    <h3 style="margin-bottom: 0; color: white;">Weekly Calendar</h3>
                """, unsafe_allow_html=True)

        col3, space, col4 = st.columns([2, 0.1,1])
        events = get_weekly_calendar_events()
        if events:
            with col3:
                df_events = []

                for e in events:
                    try:
                        start = datetime.fromisoformat(e['start'])
                        end = datetime.fromisoformat(e['end'])
                        df_events.append({
                            'Event': e['summary'],
                            'Start': start,
                            'End': end,
                            'Day': start.strftime('%A'),
                            'EventID': e.get('id'),
                            'Color': random.choice(color_palette) 
                        })
                    except Exception as ex:
                        st.warning(f"Skipping invalid event: {e}")

                df = pd.DataFrame(df_events)
                df.sort_values(by="Start", inplace=True)

                # Preparamos columnas para Altair
                df["StartHour"] = df["Start"].dt.hour + df["Start"].dt.minute / 60
                df["EndHour"] = df["End"].dt.hour + df["End"].dt.minute / 60
                df["DayName"] = df["Start"].dt.strftime("%A")

                # Filtrar eventos entre 7 am y 9 pm
                df = df[(df["StartHour"] >= 7) & (df["StartHour"] <= 21)]

                chart = alt.Chart(df).mark_rect().encode(
                    x=alt.X("DayName:N", title=" ", sort=[
                        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
                    y=alt.Y("StartHour:Q", title=" ", scale=alt.Scale(domain=[7, 21])),
                    y2="EndHour:Q",
                    color=alt.Color("Color:N", scale=None),
                    tooltip=["Event", "DayName", "StartHour", "EndHour"]
                ).properties(
                    width=700,
                    height=500,
                    title=' '
                )

                st.altair_chart(chart, use_container_width=True)

            with space:
                st.markdown("<div style='height: 100%;'></div>", unsafe_allow_html=True)
                
            with col4:
                for e in df_events:
                    event_label = f"{e['Event']} ({e['Start'].strftime('%A %H:%M')})"
                    delete_key = f"del_{e.get('EventID', event_label)}"
                    if st.button(f"Delete {event_label}", key=delete_key):
                        service = get_calendar_service()
                        service.events().delete(calendarId='primary', eventId=e['EventID']).execute()
                        st.success(f"Deleted event: {e['Event']}")
                        st.rerun()
        else:
            st.info("No events scheduled.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: Journal ---

    with tab2:
        # Database connection for journals
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        # Create the journal table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                date DATE,
                content TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

        # Fetch past journal entries for the user
        cursor.execute('''
            SELECT title, date, content
            FROM journal_entries
            WHERE user_id = ?
            ORDER BY date DESC
        ''', (user_id,))
        journal_entries = cursor.fetchall()
        conn.close()

        # Display past journal entries as boxes
        if journal_entries:
            st.markdown("""
            <div style="margin-bottom: 20px;">
                <h3 style="color: #B392AC; text-align: center;">Your Past Journals</h3>
            </div>
            """, unsafe_allow_html=True)

            for title, journal_date, content in journal_entries:
                col_journal, col_delete = st.columns([0.9, 0.1]) 
                with col_journal:
                    st.markdown(f"""
                    <div style="
                        background: #f7f5f2;
                        border-radius: 10px;
                        padding: 15px;
                        margin-bottom: 10px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    ">
                        <h4 style="color: #457B9D; margin-bottom: 5px;">{title}</h4>
                        <p style="color: gray; font-size: 12px; margin-bottom: 10px;">{journal_date}</p>
                        <p style="color: #333; font-size: 14px;">{content}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_delete:
                    # Add a delete button for each journal entry
                    delete_key=f'delete_{user_id}_{title}_{journal_date}'
                    if st.button("✖", key=f"delete_{title}_{journal_date}"):
                        conn = sqlite3.connect('user_data.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                            DELETE FROM journal_entries
                            WHERE user_id = ? AND title = ? AND date = ?
                        ''', (user_id, title, journal_date))
                        conn.commit()
                        conn.close()
                        st.rerun()
        else:
            st.info("No journal entries found. Start by creating your first journal entry below!")

        # Section to create a new journal entry
        st.markdown("""
        <div style="margin-top: 20px;">
            <h3 style="color: #B392AC; text-align: center;">Create a New Journal Entry</h3>
        </div>
        """, unsafe_allow_html=True)

        # Input fields for the new journal entry
        journal_title = st.text_input("Title", placeholder="Enter the title of your journal")
        journal_date = date.today()
        journal_content = st.text_area("Journal Content", placeholder="Write your thoughts here...")

        # Save the new journal entry
        if st.button("Save Journal Entry"):
            if journal_title.strip() and journal_content.strip():
                conn = sqlite3.connect('user_data.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO journal_entries (user_id, title, date, content)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, journal_title.strip(), journal_date, journal_content.strip()))
                conn.commit()
                conn.close()
                st.success("Journal entry saved successfully!")
                st.rerun()  # Refresh the page to show the new entry
            else:
                st.error("Please fill in both the title and content of your journal.")

# -------------------- App Initialization --------------------

create_database()
update_database_schema()

if 'page' not in st.session_state:
    st.session_state['page'] = 'sign_in'

if st.session_state['page'] == 'sign_in':
    sign_in()
elif st.session_state['page'] == 'create_account':
    create_account()
elif st.session_state['page'] == 'onboarding':
    onboarding()
elif st.session_state['page'] == 'daily_stress_survey':
    daily_stress_survey()
elif st.session_state['page'] == 'main':
    main_page()