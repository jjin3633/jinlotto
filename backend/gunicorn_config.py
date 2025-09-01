# Gunicorn 설정 파일
bind = "0.0.0.0:10000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
