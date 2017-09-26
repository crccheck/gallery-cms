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

build: ## Build assets
	npm run build

build/prod:
	# TODO
	# autoprefixer
	# uglify

dev:
	npm run dev

# WIP If you have trouble with this, run `add2virtualenv gallery`
test: ## Run test suite
	pytest --cov

docker/release: ## Build and push a new release to Docker Hub
docker/release: build
	docker-compose build
	docker tag gallerycms_web crccheck/gallery-cms
	docker push crccheck/gallery-cms

docker/test: clean
	docker-compose build
	docker-compose run --rm web make test
