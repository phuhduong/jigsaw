.PHONY: check check-backend check-mcp check-frontend

check: check-backend check-mcp check-frontend

check-backend:
	cd backend && .venv/bin/python -m unittest discover -s tests

check-mcp:
	cd mcp-server && npm test

check-frontend:
	cd frontend && yarn test && yarn typecheck && yarn build
