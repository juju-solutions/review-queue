PROJECT=reviewqueue

PYHOME=.venv/bin
PYTHON=$(PYHOME)/python


all: test

clean:
	rm -rf MANIFEST dist/* $(PROJECT).egg-info .coverage
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf .venv
	rm -rf deps

deps:
	# Download deps to local cache
	pip wheel -r requirements.txt -w deps/

test: .venv
	@echo Starting tests...
	$(PYHOME)/tox

.venv:
	# install deps for theblues (https://github.com/juju/theblues#installation)
	#sudo add-apt-repository ppa:yellow/ppa -y
	#sudo apt-get update -qy
	#sudo apt-get install -qy libmacaroons0 python-macaroons libsodium13
	# create virtualenv, install app deps
	sudo apt-get install -qy virtualenv libpq-dev python-dev
	virtualenv --never-download .venv

	$(PYHOME)/pip install --no-index -f deps/ -r requirements.txt
	$(PYHOME)/pip install --no-index -f deps/ -e .

serve: .venv
	$(PYHOME)/initialize_db development.ini
	$(PYHOME)/pserve --reload development.ini

celery: .venv
	$(PYHOME)/celery -A reviewqueue.celerycfg worker -l info -B

smtp:
	# Runs a local smtp server for testing email features
	python -m smtpd -n -c DebuggingServer localhost:2525

.PHONY: clean
