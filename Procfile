web: flask db upgrade; gunicorn -k flask_sockets.worker bunker:app
worker: rq worker game_tasks
