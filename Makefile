PROJECT=reviewqueue

PYHOME=.venv/bin
PYTHON=$(PYHOME)/python


all: test

clean:
	rm -rf MANIFEST dist/* $(PROJECT).egg-info .coverage
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf .venv

test: .venv
	@echo Starting tests...
	$(PYHOME)/tox

.venv:
	sudo apt-get install -qy python-virtualenv libpq-dev python-dev
	virtualenv .venv
	$(PYHOME)/pip install -U pip setuptools
	$(PYHOME)/pip install -e .

serve: .venv
	$(PYHOME)/initialize_db development.ini
	$(PYHOME)/pserve --reload development.ini


.PHONY: clean
