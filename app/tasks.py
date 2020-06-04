import json
from rq import get_current_job
from datetime import datetime, timezone, timedelta
from app import create_app, db
from app.models import Game, TerminalMessage, RadioMessage


app = create_app()
app.app_context().push()


def start_game():
    print('start game')
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

        time = game.update(now)
        text_data = json.dumps({
            'type': 'game_state',
            'time': time,
            'timer_run': game.gameStarted,
            'game_state': game.state
        })
        db.session.commit()

        app.redis.publish(game_name, text_data)


def end_game():
    print('end game')
    game_name = "testGame"
    now = datetime.utcnow()

    game = Game.query.filter_by(name=game_name).first()
    if game is not None:
        game.roundEndData = now
        time = game.update(now)
        game.gameStarted = False
        game.state = 'stop'

        # Send message to WebSocket
        text_data = json.dumps({
            'type': 'game_state',
            'time': time,
            'timer_run': game.gameStarted,
            'game_state': game.state
        })
        db.session.commit()

        app.redis.publish(game_name, text_data)


def pause_game():
    print('pause game')
    game_name = "testGame"
    now = datetime.utcnow()

    game = Game.query.filter_by(name=game_name).first()
    if game is not None:
        time = game.update(now)
        game.gameStarted = False
        game.state = 'pause'

        # Send message to WebSocket
        text_data = json.dumps({
            'type': 'game_state',
            'time': time,
            'timer_run': game.gameStarted,
            'game_state': game.state
        })
        db.session.commit()

        app.redis.publish(game_name, text_data)


def clear_game():
    print('clear game')
    game_name = "testGame"
    game = Game.query.filter_by(name=game_name).first()
    if game is not None:
        TerminalMessage.query.filter_by(game_id=game.id).delete()
        RadioMessage.query.filter_by(game_id=game.id).delete()
        db.session.commit()
        text_data = json.dumps({
            'type': 'clear_game',
        })
        app.redis.publish(game_name, text_data)


def terminal_message(message):
    print('check terminal message')
    game_name = "testGame"
    now = datetime.utcnow()

    game = Game.query.filter_by(name=game_name).first()
    if game is not None:
        # check message
        code_str_list = game.secretCode.split()
        code = list(map(int, code_str_list))

        try:
            temp = message.split(':')
            author = temp[0]
            text = temp[1]
            number_strings = text.split()
        except AttributeError:
            author = "?"
            text = message
            number_strings = []

        match_counter = 0
        for number_string in number_strings:
            print(number_string)
            try:
                number = int(number_string)
                print(number)
                if number in code:
                    match_counter += 1
            except ValueError:
                pass

        print(match_counter)
        if match_counter == len(code):
            answer = 'Вы угадали код'
        elif match_counter > 0:
            answer = 'Количество совпадений: ' + str(match_counter)
        else:
            answer = 'Совпадений нет'

        terminal_message = TerminalMessage(game_id=game.id,
                                           time=now,
                                           author=author,
                                           text=text,
                                           answer=answer)
        db.session.add(terminal_message)
        app.redis.publish(game_name, terminal_message.get_json())

        # reset round
        game.roundEndData = now + timedelta(seconds=game.period)
        game.left_time = game.period
        db.session.commit()
        text_data = json.dumps({
            'type': 'game_state',
            'time': game.left_time,
            'timer_run': game.gameStarted,
            'game_state': game.state
        })
        app.redis.publish(game_name, text_data)


def radio_receive(message):
    print('check transmitter message')
    game_name = "testGame"
    now = datetime.utcnow()

    game = Game.query.filter_by(name=game_name).first()
    if game is not None:
        try:
            temp = message.split(':')
            author = temp[0]
            text = temp[1]
        except AttributeError:
            author = "?"
            text = message

        radio_message = RadioMessage(game_id=game.id,
                                     time=now,
                                     author=author,
                                     text=text,)
        db.session.add(radio_message)
        db.session.commit()
        app.redis.publish(game_name, radio_message.get_json())
