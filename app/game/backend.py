import json
import gevent
from app import sockets
from config import Config
from redis import Redis
from flask import current_app


GAME_CHANNEL = 'testGame'

redis = Redis.from_url(Config.REDIS_URL)


class GameBackend(object):
    def __init__(self):
        self.timer_clients = list()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(GAME_CHANNEL)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                yield data.decode()

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        self.timer_clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            self.timer_clients.remove(client)

    def run(self):
        for json_data in self.__iter_data():
            # for client in timer_clients:
            for client in self.timer_clients:
                gevent.spawn(self.send, client, json_data)

    def start(self):
        """Maintains Redis subscription in the background."""
        gevent.spawn(self.run)


game_backend = GameBackend()
game_backend.start()


@sockets.route('/ws/game/state')
def game_socket(ws):
    game_backend.register(ws)
    while not ws.closed:
        gevent.sleep(0.1)


@sockets.route('/ws/game/command')
def game_socket(ws):
    while not ws.closed:
        gevent.sleep(0.1)
        message = ws.receive()
        if message:
            print(u'Inserting message: {}'.format(message))
            data = json.loads(message)

            command = data.get('command')
            if command == 'start_game':
                current_app.task_queue.enqueue('app.tasks.start_game')
                # game_backend.start_game()
            elif command == 'stop_game':
                current_app.task_queue.enqueue('app.tasks.end_game')
                # game_backend.end_game()
            elif command == 'pause_game':
                current_app.task_queue.enqueue('app.tasks.pause_game')
            elif command == 'clear_game':
                current_app.task_queue.enqueue('app.tasks.clear_game')

            terminal_message = data.get('terminal_send')
            if terminal_message:
                current_app.task_queue.enqueue('app.tasks.terminal_message', terminal_message)

            radio_message = data.get('radio_send')
            if radio_message:
                current_app.task_queue.enqueue('app.tasks.radio_receive', radio_message)
