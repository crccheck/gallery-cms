help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"

install: ## Install requirements
	@[ -n "${VIRTUAL_ENV}" ] || (echo "ERROR: This should be run from a virtualenv" && exit 1)
	pip install -r requirements.txt

.PHONY: requirements.txt
requirements.txt: ## Regenerate requirements.txt
	pip-compile > $@

clean: ## Delete transient files
	-find . -type d -name "__pycache__" -exec rm -rf {} \;

test: ## Run test suite
	pytest --cov

docker/release: ## Build and push a new release to Docker Hub
	grunt build
	docker-compose build
	docker tag gallerycms_web crccheck/gallery-cms
	docker push crccheck/gallery-cms

docker/test: clean
	docker-compose build
	docker-compose run web make test
