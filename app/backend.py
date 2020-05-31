from app import app, db
from config import Config
from flask_sockets import Sockets
# from flask_socketio import SocketIO
from redis import Redis
import gevent
from datetime import datetime, timezone, timedelta
import json

from app.models import Game
from app import timer_clients

GAME_CHANNEL = 'game'
sockets = Sockets(app)
# socketio = SocketIO(app)
redis = Redis.from_url(Config.REDIS_URL)


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

# @socketio.on('my event')
# def handle_my_custom_event(json, methods=['GET', 'POST']):
#     print('received my event: ' + str(json))
#     socketio.emit('my response', json, callback=messageReceived)


class GameBackend(object):
    def __init__(self):
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(GAME_CHANNEL)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                app.logger.info(u'Sending message: {}'.format(data))
                yield data

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        timer_clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            timer_clients.remove(client)

    def run(self):
        for data in self.__iter_data():
            for client in self.clients:
                gevent.spawn(self.send, client, data)

    def start(self):
        """Maintains Redis subscription in the background."""
        gevent.spawn(self.run)

    def start_game(self):
        game_name = "testGame"
        now = datetime.utcnow()

        game = Game.query.filter_by(name=game_name).first()
        if game is not None:
            game.gameStarted = True
            if game.state == 'stop':
                game.roundEndData = now + timedelta(seconds=game.period)
            elif game.state == 'pause':
                game.roundEndData = now + timedelta(seconds=game.left_time)
            game.state = 'start'
            if game.startData is None:
                game.startData = now

            # Send message to WebSocket
            time = game.update(now)
            text_data = json.dumps({
                'time': time,
                'timer_run': game.gameStarted,
                'game_state': game.state
            })
            for client in timer_clients:
                gevent.spawn(self.send, client, text_data)

            db.session.add(game)
            db.session.commit()

    def end_game(self):
        game_name = "testGame"
        now = datetime.utcnow()

        game = Game.query.filter_by(name=game_name).first()
        if game is not None:
            game.gameStarted = False
            game.state = 'stop'
            game.roundEndData = now
            time = game.update(now)

            # Send message to WebSocket
            text_data = json.dumps({
                'time': time,
                'timer_run': game.gameStarted,
                'game_state': game.state
            })
            for client in timer_clients:
                gevent.spawn(self.send, client, text_data)

            db.session.add(game)
            db.session.commit()

    def pause_game(self):
        game_name = "testGame"
        now = datetime.utcnow()

        game = Game.query.filter_by(name=game_name).first()
        if game is not None:
            time = game.update(now)
            game.gameStarted = False
            game.state = 'pause'

            # Send message to WebSocket
            text_data = json.dumps({
                'time': time,
                'timer_run': game.gameStarted,
                'game_state': game.state
            })
            for client in timer_clients:
                gevent.spawn(self.send, client, text_data)

            db.session.add(game)
            db.session.commit()


game_backend = GameBackend()
game_backend.start()


@sockets.route('/ws/game')
def timer_sync(ws):
    game_backend.register(ws)
    while not ws.closed:
        gevent.sleep(0.1)
        message = ws.receive()
        if message:
            data = json.loads(message)
            command = data.get('command')
            if command == 'start_game':
                game_backend.start_game()
            elif command == 'stop_game':
                game_backend.end_game()
            elif command == 'pause_game':
                game_backend.pause_game()
