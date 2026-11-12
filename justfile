
run-as-agent:
	docker build -t laya-agent .
	docker run -ti --rm --name laya-agent -p 8080:8080 laya-agent -c "/app/laya-as-agent-api/run-agent.sh"