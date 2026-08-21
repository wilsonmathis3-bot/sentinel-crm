# Sentinel CRM

A focused MVP CRM with AI layer and Natural Language Interface.

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Stack

- **Backend:** FastAPI + SQLite
- **Frontend:** React
- **AI Layer:** Rule-based Python agents
- **NLI:** Text-to-SQL converter

## Features

- Contact database with interaction history
- Deal pipeline (Kanban view)
- Task management
- Dashboard with metrics
- Prospecting agent (lead scoring)
- Nurturing agent (follow-up timing)
- Health score calculation
- Natural language queries
