.PHONY: init
init:
	python -m pip install --upgrade pip

.PHONY: install
install:
	python -m pip install --upgrade .

.PHONY: install-dev
install-dev:
	python -m pip install --editable .[dev,test]
	pre-commit install

.PHONY: coverage
coverage:
	tox -p

.PHONY: docker-test
docker-test:
	docker rm -f pd-util-tester
	docker rmi -f pd-util-test
	docker build -f docker/docker-test-runner -t pd-util-test .
	docker run -m 128m --name pd-util-tester pd-util-test
	docker cp pd-util-tester:pd-utils/coverage.json .

.PHONY: build-dist
build-dist:
	python -m pip install --upgrade build
	python -m build

.PHONY: clean
clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '.mypy_cache' -exec rm -rf {} +
	rm -rf .tox
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .coverage.*
	rm -f coverage.xml
	rm -f coverage.json
	find . -name '.pytest_cache' -exec rm -rf {} +
	rm -rf dist
	rm -rf build
