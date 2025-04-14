# Include the .env file (make sure it exists and is properly formatted)
ifneq (,$(wildcard .env))
  include .env
  export
endif

.PHONY: check
check:
	poetry -P api run pre-commit run --all-files

.PHONY: check-full
check-full:
	poetry -P api run pre-commit run --all-files

.PHONY: check-staged
	poetry -P api run pre-commit run --staged-files

.PHONY: run-api
run-api:
	cd api && \
		poetry run python -m app

.PHONY: run-frontend
run-frontend:
	cd frontend && \
		npm run start
