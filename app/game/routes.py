# -*- coding: utf-8 -*-
import os
from flask import render_template, redirect, url_for, session
from flask import flash
from flask import send_from_directory
from app import db
from app.game.forms import CharacterForm, SecretCodeForm
from app.models import Game, TerminalMessage, RadioMessage
from app.game import bp

from datetime import datetime
from flask import current_app

game_name = "testGame"


@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@bp.route('/')
def foo():
    return redirect(url_for('game.bunker_hall'))


@bp.route('/error')
def error():
    # return "error"
    return os.environ.get('DATABASE_URL')


@bp.route('/game/character', methods=['GET', 'POST'])
def character_settings():
    form = CharacterForm()
    if form.validate_on_submit():
        session['character_name'] = form.character_name.data
        return redirect(url_for('game.bunker_hall'))
    return render_template('character.html', form=form)


@bp.route('/game/secret-code', methods=['GET', 'POST'])
def secret_code():
    form = SecretCodeForm()
    if form.validate_on_submit():
        game = Game.query.filter_by(name=game_name).first()
        if game is None:
            flash('Game is not created')
            return redirect(url_for('game.error'))
        game.secretCode = form.secretCode.data
        db.session.add(game)
        db.session.commit()
        return redirect(url_for('game.game_admin'))
    return render_template('secret_code.html', form=form)


@bp.route('/game/bunker_hall')
def bunker_hall():
    if 'character_name' not in session:
        return redirect(url_for('game.character_settings'))
    character_name = session['character_name']

    game = Game.query.filter_by(name=game_name).first()
    if game is None:
        flash('Game is not created')
        return redirect(url_for('game.error'))

    return render_template('bunker_hall.html',
                           time=game.update(datetime.utcnow()),
                           timer_run=game.gameStarted,
                           character_name=character_name,)


@bp.route('/game/bunker_terminal')
def bunker_terminal():
    if 'character_name' not in session:
        return redirect(url_for('game.character_settings'))
    character_name = session['character_name']

    game = Game.query.filter_by(name=game_name).first()
    if game is None:
        flash('Game is not created')
        return redirect(url_for('game.error'))

    history = []
    message_objects = TerminalMessage.query.filter_by(game_id=game.id)
    for message in message_objects:
        history.append(message.get_json())

    return render_template('bunker_terminal.html',
                           time=game.update(datetime.utcnow()),
                           timer_run=game.gameStarted,
                           character_name=character_name,
                           terminal_history=history,)


@bp.route('/game/bunker_radio_room')
def bunker_radio_room():
    if 'character_name' not in session:
        return redirect(url_for('game.character_settings'))
    character_name = session['character_name']

    game = Game.query.filter_by(name=game_name).first()
    if game is None:
        flash('Game is not created')
        return redirect(url_for('game.error'))

    radio_history = []
    message_objects = RadioMessage.query.filter_by(game_id=game.id)
    for message in message_objects:
        radio_history.append(message.get_json())

    return render_template('bunker_radio_room.html',
                           time=game.update(datetime.utcnow()),
                           timer_run=game.gameStarted,
                           character_name=character_name,
                           radio_history=radio_history,)


@bp.route('/game/admin')
def game_admin():
    game = Game.query.filter_by(name=game_name).first()
    if game is None:
        game = Game(name=game_name,
                    state='stop',
                    announcedData=datetime.utcnow(),
                    gameStarted=False)
        db.session.add(game)
        db.session.commit()
        print("create new Game")

    terminal_history = []
    message_objects = TerminalMessage.query.filter_by(game_id=game.id)
    for message in message_objects:
        terminal_history.append(message.get_json())

    radio_history = []
    message_objects = RadioMessage.query.filter_by(game_id=game.id)
    for message in message_objects:
        radio_history.append(message.get_json())

    return render_template('game_admin.html',
                           time=game.update(datetime.utcnow()),
                           timer_run=game.gameStarted,
                           game_state=game.state,
                           secret_code=game.secretCode,
                           terminal_history=terminal_history,
                           radio_history=radio_history,)
