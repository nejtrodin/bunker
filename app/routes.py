# -*- coding: utf-8 -*-
import os
from flask import render_template, redirect, url_for, session
from flask import flash
from flask import send_from_directory
from app import app, db
from app.forms import CharacterForm
from app.models import Game

from datetime import datetime, timezone


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/index')
def index():
    return "error"


@app.route('/game/character', methods=['GET', 'POST'])
def character_settings():
    form = CharacterForm()
    if form.validate_on_submit():
        session['character_name'] = form.character_name.data
        return redirect(url_for('bunker_hall'))
    return render_template('character.html', form=form)


@app.route('/game/bunker_hall')
def bunker_hall():
    game_name = "testGame"

    if 'character_name' not in session:
        return redirect(url_for('character_settings'))
    character_name = session['character_name']

    game = Game.query.filter_by(name=game_name).first()
    if game is None:
        flash('Game is not created')
        return redirect(url_for('index'))

    return render_template('bunker_hall.html',
                           time=game.update(datetime.utcnow()),
                           timer_run=game.gameStarted,
                           character_name=character_name,)


@app.route('/game/bunker_terminal')
def bunker_terminal():
    game_name = "testGame"

    if 'character_name' not in session:
        return redirect(url_for('character_settings'))
    character_name = session['character_name']

    game = Game.query.filter_by(name=game_name).first()
    if game is None:
        flash('Game is not created')
        return redirect(url_for('index'))

    return render_template('bunker_terminal.html',
                           time=game.update(datetime.utcnow()),
                           timer_run=game.gameStarted,
                           character_name=character_name,)


@app.route('/game/admin')
def game_admin():
    game_name = "testGame"

    game = Game.query.filter_by(name=game_name).first()
    if game is None:
        game = Game(name=game_name,
                    state='stop',
                    announcedData=datetime.utcnow(),
                    gameStarted=False)
        db.session.add(game)
        db.session.commit()
        print("create new Game")

    return render_template('game_admin.html',
                           time=game.update(datetime.utcnow()),
                           timer_run=game.gameStarted,
                           secret_code=game.secretCode,)
