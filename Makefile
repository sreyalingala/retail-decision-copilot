.PHONY: install dev test lint seed

install:
	npm install

dev:
	npm run dev -w @rdc/web

test:
	npm run test -ws

lint:
	npm run lint -ws

seed:
	npm run seed -w @rdc/api

