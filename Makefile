.PHONY: up import export commit checkout restore

# 1️⃣ only docker no versions
up:
	docker compose up -d postgres n8n app neo4j nginx

# 2️⃣ import workflow from git to n8n
import:
	docker compose run --rm n8n-importer

# 3️⃣ export workflow from n8n to git and make commit
commit:
	docker compose run --rm n8n-exporter
	git add n8n_workflows
	git commit -m "update workflows $$(date +%Y-%m-%dT%H:%M:%S)"
	git push

# 4️⃣ backup (checkout)
checkout:
	@if [ -z "$(commit)" ]; then \
		echo "Usage: make checkout commit=<hash>"; \
		exit 1; \
	fi
	git checkout $(commit)

# 5️⃣ restart docker import git current version n8n
restore: checkout
	docker compose down
	docker compose up -d postgres
	sleep 5
	docker compose run --rm n8n-importer
	docker compose up -d n8n app neo4j nginx