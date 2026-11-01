# CareerPilot — Smart Job Recommendation System

A demo-ready B.Tech mini-project prototype built with HTML, CSS, Bootstrap 5, Python Flask, and SQLite.

## Features
- Registration and login with hashed passwords
- Profile editing and skills management
- Seeded sample job database
- Job search by keyword, location, and type
- Skill-overlap match percentage and ranked recommendations
- Missing-skill analysis
- Save/unsave jobs
- SQLite database created automatically on first run

## Run on Windows
1. Install Python 3.10+ from https://www.python.org/downloads/ and enable **Add Python to PATH**.
2. Extract the ZIP, then open the `CareerPilot` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
5. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt terminal and run:
   ```bat
   .venv\Scripts\activate.bat
   ```
6. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Start the app:
   ```powershell
   python app.py
   ```
8. Open the local URL printed in the terminal, usually http://127.0.0.1:5000.

## Suggested demo
1. Register with a demo email and password (6+ characters).
2. Open Profile and enter skills such as `Python, SQL, Flask, Git, HTML`.
3. Open Dashboard to show ranked recommendations and match percentages.
4. Open Find Jobs and try filters.
5. Open a job to show matched and missing skills.
6. Save a job, then show it under Saved Jobs.
7. Log out and log in again to demonstrate authentication.

## How matching works
For each job:
`match percentage = (number of user's skills matching required job skills / number of required skills) × 100`

The score is an explainable baseline algorithm. It is not an AI/ML model and does not use live job listings. Jobs are sample records seeded into the local SQLite database. Resume parsing, external job APIs, and AI/NLP features are not implemented in this prototype.

## Reset demo data
Stop the server, delete `instance/careerpilot.db` if present, then run `python app.py` again. The database will be recreated and seeded.
