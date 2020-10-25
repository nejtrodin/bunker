import json
from datetime import datetime, timedelta
from pytz import utc
from app import create_app, db
from app.models import Game, TerminalMessage, RadioMessage
from apscheduler.schedulers.base import JobLookupError


app = create_app()


def game_update(game_id, new_state=None):
    with app.app_context():
        game = Game.query.filter_by(id=game_id).first()
        if game is not None:
            now = datetime.utcnow()
            job_id = 'game_' + str(game_id)

            if new_state == 'start':
                print('start game')
                game.gameStarted = True
                if game.state == 'stop':
                    game.roundEndData = now + timedelta(seconds=game.period)
                elif game.state == 'pause':
                    game.roundEndData = now + timedelta(seconds=game.left_time)
                game.state = 'start'
                if game.startData is None:
                    game.startData = now
            elif new_state == 'stop':
                print('stop game')
                game.roundEndData = now
                try:
                    app.apscheduler.remove_job(job_id)
                except JobLookupError:
                    pass
            elif new_state == 'pause':
                print('pause game')
                game.update(now)
                game.state = 'pause'
                game.gameStarted = False
                try:
                    app.apscheduler.remove_job(job_id)
                except JobLookupError:
                    pass

            timer_value = game.update(now)
            if game.gameStarted and timer_value > 0:
                # schedule next update
                delay = timer_value
                if timer_value > 20:
                    delay = 20

                next_date = now + timedelta(seconds=delay);
                app.apscheduler.add_job(id=job_id,
                                        func=game_update,
                                        trigger='date',
                                        run_date=utc.fromutc(next_date),
                                        kwargs={'game_id': game_id})

            text_data = json.dumps({
                'type': 'game_state',
                'time': round(timer_value),
                'timer_run': game.gameStarted,
                'game_state': game.state
            })
            app.redis.publish(game.name, text_data)

            db.session.commit()


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
        game_code_list = game.secretCode.split()
        target_match = len(game_code_list)

        # сообщение вида "автор: код терминала"
        try:
            temp = message.split(':')
            author = temp[0]
            text = temp[1]
            user_code_list = text.split()
        except AttributeError:
            author = "?"
            text = message
            user_code_list = []

        match_counter = 0
        for user_code in user_code_list:
            try:
                game_code_list.remove(user_code)
                match_counter += 1
            except ValueError:
                pass

        if match_counter == target_match:
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
