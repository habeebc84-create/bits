# SIGNAL HUNTER X — one-command local setup
.PHONY: backend frontend test seed

backend:
	cd backend && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm install && npm run dev

test:
	cd backend && python -m pytest

seed:
	cd backend && python -m app.seed_demo
