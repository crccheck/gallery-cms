help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"

install: ## Install requirements
	poetry install
	npm install

clean: ## Delete transient files
	-find . -type d -name "__pycache__" -exec rm -rf {} \;

build: ## Build assets
	npm run build

dev:
	# npm run dev
	uvicorn --reload --host 0.0.0.0 --port 8081 gallery.server:app

# WIP If you have trouble with this, run `add2virtualenv gallery`
test: ## Run test suite
	pytest --cov

tdd:
	ptw -- -sx --disable-pytest-warnings

docker/build: build
	docker-compose build
