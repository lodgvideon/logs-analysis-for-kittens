


.PHONY: deps
deps:
	brew update
	brew install goose
	brew install docker-compose



.PHONY: ch-up
ch-up:
	docker-compose -f ./docker/docker-compose.yml -p ch-site-logs up -d
	echo "Starting local CH Server: Ports: 8123,9000 have to be opened!"

.PHONY: ch-down
ch-down:
	docker-compose -f ./docker/docker-compose.yml -p ch-site-logs down

.PHONY: ch-status
ch-status:
	docker-compose -p ch-site-logs ps

.PHONY: migrate
migrate-up:
	goose -dir  ./migrations clickhouse "tcp://default:12345@127.0.0.1:9000" up

.PHONY: down
migrate-down:
	goose -dir  ./migrations clickhouse "tcp://default:12345@127.0.0.1:9000" down