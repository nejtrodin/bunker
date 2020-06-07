import json
import gevent
from app import sockets
from config import Config
from redis import Redis
from app.tasks import game_update, clear_game, terminal_message, radio_receive

GAME_CHANNEL = 'testGame'
game_id = 1

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
            data = json.loads(message)

            command = data.get('command')
            if command == 'start_game':
                game_update(game_id=game_id, new_state='start')
            elif command == 'stop_game':
                game_update(game_id=game_id, new_state='stop')
            elif command == 'pause_game':
                game_update(game_id=game_id, new_state='pause')
            elif command == 'clear_game':
                clear_game()

            terminal_send = data.get('terminal_send')
            if terminal_send:
                terminal_message(terminal_send)

            radio_send = data.get('radio_send')
            if radio_send:
                radio_receive(radio_send)
