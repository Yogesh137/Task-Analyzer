# Smart Task Analyzer

## Overview
A small Django-based application that scores and prioritizes tasks. It accepts a list of tasks (JSON or form input) and returns tasks sorted by priority score. The scoring algorithm balances urgency, importance, effort (quick wins), and dependencies. The app supports multiple weighting strategies: Fastest Wins, High Impact, Deadline Driven, and Smart Balance.

## Setup (quick)
1. Create and activate venv:
   - `python -m venv venv`
   - `source venv/bin/activate` (Windows: `.\venv\Scripts\activate`)
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run migrations:
   - `python manage.py makemigrations`
   - `python manage.py migrate`
4. Run server:
   - `python manage.py runserver`
5. Open `frontend/index.html` in a browser and point to `http://127.0.0.1:8000` backend.

## API
- `POST /api/tasks/analyze/?strategy=<strategy>`  
  Body: JSON array of tasks. Returns JSON with sorted tasks and computed scores.
- `POST /api/tasks/suggest/?strategy=<strategy>`  
  Returns top-3 task suggestions with explanations.

## Data format (example)
```json
[{
  "id":"1","title":"Finish report","due_date":"2025-11-30","importance":8,"estimated_hours":3,"dependencies":[]
}]
