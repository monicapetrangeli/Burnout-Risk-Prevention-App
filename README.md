# Exhale: An AI-Powered Wellness Platform for Burnout Prevention
## Overview
Exhale is a mental wellness application built as the final project for the Prototyping with AI course in the MSc in Business Analytics at ESADE. It was designed with one clear goal: to help individuals monitor and manage their risk of burnout through AI-driven insights and personalised, data-informed interventions.

Developed using Python and Streamlit, Exhale leverages wearable data, daily self-assessments, intelligent scheduling, and predictive modelling to create a wellness companion that not only identifies rising stress levels but actively helps users restore balance.

## Motivation & Vision
The idea for Exhale emerged from a deeply personal place: our team was juggling demanding academic workloads and the weight of exams, and we began to recognise the creeping signs of burnout in ourselves. Yet, like many others, we weren’t sure how to manage it—or even how to measure it.

Exhale was born from this experience, with the vision of becoming a supportive, accessible tool for students and working professionals alike. At its core, Exhale embodies the belief that mental health is health, and that prevention is more powerful than cure.

## Key Features
- *Daily Burnout Prediction*
    - Using a combination of self-reported inputs and contextual data (workload, stress levels, exercise, sleep), the app calculates a personalised burnout risk score.

- *Smart Wellness Recommendations*
    - Based on the user’s burnout score, Exhale offers science-based activities across emotional, physical, mental, and restorative dimensions—and allows users to schedule them seamlessly into their day.

- *Fitbit Integration*
    - Users can connect their Fitbit to passively sync activity data, enhancing the accuracy of burnout prediction and minimising reliance on manual input.

- *Intelligent Scheduling*
    - Through Google Calendar integration, Exhale can schedule wellness tasks around the user's existing obligations.

- *To-Do Lists and Journal Tracking*
    - The app supports reflective journaling and task management, creating a space for both productivity and introspection.

- *Burnout History Dashboard*
    - Users can visualise their burnout trends over time and correlate them with habits and behaviour.

## Technical Highlights
1. Streamlit Frontend for a reactive and interactive web experience.

2. SQLite Database to maintain persistent user data and avoid a stateless design.

3. Google Calendar & Fitbit API Integrations for a seamless connection with external tools.

4. Custom Burnout Prediction Model, using weighted factors such as age, stress levels, work hours, sleep, and lifestyle inputs.

## Development Insights
This project was developed in a team of four: Carlota, Sofia, Juan Pablo, and myself. I contributed the original idea and built the backend structure while working together with the rest on the aesthetic of the app.

The greatest technical challenge was ensuring smooth integration between our multiple APIs and internal modules. But the experience proved deeply rewarding: I developed a stronger attention to detail, improved my prioritisation skills, and learned how to balance ambitious features with the constraints of a real-world development timeline.

## Roadmap
As part of the next evolution of Exhale, we plan to:

- *Add a Mood Calendar:* Enable users to visualise emotional trends over time based on daily mood inputs.

- *Refine the Burnout Prediction Model:* Revisit initial assumptions (e.g., the impact of age, feature weightings) to improve accuracy.

- *Deploy the App Online:* Make Exhale publicly accessible from anywhere and enhance Fitbit connectivity.

- *Personalise Task Scheduling:* Use onboarding preferences to tailor wellness tasks and improve user engagement.

- *Enable Passive Emotion Tracking:* Analyse daily journal entries to extract emotions and keywords — offering an honest, non-intrusive alternative to surveys.

## Conclusion
Exhale is more than a class project—it’s a prototype with potential. As mental health continues to gain attention in educational and workplace environments, tools like Exhale can play a meaningful role in promoting well-being through data, design, and empathy.

## P.S.
To run Exhale locally, please ensure the following:

- Add your Fitbit Client ID and Secret to the fitbit_data.py file. You can obtain these by registering an app at dev.fitbit.com.

- Set up your Google Calendar API by creating a credentials.json file as instructed in the official Google Calendar API guide. This file is required for scheduling features to function.

## Credits
Exhale was developed by:

- [@monicapetrangeli](https://github.com/monicapetrangeli) – Concept, system architecture, aesthetic
- [@carlotatejeda](https://github.com/carlotatejeda) – FitBit API integration, aesthetic
- [@SofiaGitHub](https://github.com/SofiaGitHub) – Features finalization, aesthetic
- [@JuanPabloGitHub](https://github.com/JuanPabloGitHub) – Google Calendar API integration, aesthetic
