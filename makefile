inference:
	docker build -t gpt-api . && docker run -it --rm --gpus all --name gpt-api -p 8000:8000 gpt-api

clean:
	docker system prune
