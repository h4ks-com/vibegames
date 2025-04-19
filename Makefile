# Include the .env file (make sure it exists and is properly formatted)
ifneq (,$(wildcard api/.env))
  include api/.env
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
		PORT=3000 npm run start

.PHONY: run-webcapture
run-webcapture:
	docker run -it --network="host" \
		-e API_TOKEN=$(CAPTURE_API_KEY) \
		-e PORT=$(lastword $(subst :, ,$(subst ",,$(CAPTURE_API_URL)))) \
		--restart=always \
		-v tmp-data:/tmp/capture \
		mattfly/webcapture-service

.PHONY: run
run:
	@$(MAKE) -j run-api run-frontend run-webcapture

