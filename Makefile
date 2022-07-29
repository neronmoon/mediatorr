.PHONY:
	build

build:
	git pull
	docker build -t mediatorr:latest .
