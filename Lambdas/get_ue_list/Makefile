.ONESHELL:
.PHONY: help check clean fetch-dependencies docker-build build-lambda-package

SHELL=/bin/zsh
# Note that the extra activate is needed to ensure that the activate floats env to the front of PATH
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate
CONDA_SHOW=source $$(conda info --base)/etc/profile.d/conda.sh ; conda env list


help:
	@python -c 'import fileinput,re; \
	ms=filter(None, (re.search("([a-zA-Z_-]+):.*?## (.*)$$",l) for l in fileinput.input())); \
	print("\n".join(sorted("\033[36m  {:25}\033[0m {}".format(*m.groups()) for m in ms)))' $(MAKEFILE_LIST)

check:		## print versions of required tools
	@docker --version
	@docker-compose --version
	@python3 --version

clean:		## delete pycache, build files
	@rm -rf build build.zip
	@rm -rf __pycache__

fetch-dependencies:		## download chromedriver, headless-chrome to `./bin/`
	@mkdir -p bin/

	# Get chromedriver
	curl -SL https://chromedriver.storage.googleapis.com/86.0.4240.22/chromedriver_linux64.zip > chromedriver.zip
	unzip chromedriver.zip -d bin/

	# Get Headless-chrome
	curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-57/stable-headless-chromium-amazonlinux-2017-03.zip > headless-chromium.zip
	unzip headless-chromium.zip -d bin/

	# Clean
	@rm headless-chromium.zip chromedriver.zip

docker-build:		## create Docker image
	docker-compose build

docker-run:			## run `src.lambda_function.lambda_handler` with docker-compose
	docker-compose run lambda src.lambda_function.lambda_handler

build-lambda-package:		## prepares zip archive for AWS Lambda deploy (-> build/build.zip)
	mkdir build
	cp -r src build/.
	cp -r bin build/.
	cp -r lib build/.
	pip install -r requirements.txt -t build/lib/.
	cd build; zip -9qr build.zip .
	cd ..
	cp build/build.zip .
	rm -rf build
	
## scp -i appworks_school_hsin_yi.pem ec2-user@54.179.123.235:UFC/Lambdas/get_ue_list/build.zip Documents/GitHub/UFC/Lambdas/get_ue_list/

test:		## prepares zip archive for AWS Lambda deploy (-> build/build.zip)	
	$(CONDA_ACTIVATE) python36 && $(CONDA_SHOW)