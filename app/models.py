from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), index=True)
    announcedData = db.Column(db.DateTime)
    period = db.Column(db.Integer, default=600)
    left_time = db.Column(db.Integer, default=0)
    state = db.Column(db.String(20), default='stop')
    gameStarted = db.Column(db.Boolean, default=False)
    startData = db.Column(db.DateTime, nullable=True)
    roundEndData = db.Column(db.DateTime, nullable=True)
    secretCode = db.Column(db.String(200), index=True, default='1 2 3 4')

    def __repr__(self):
        return '<Game {}>'.format(self.name)

    def update(self, now):
        if self.gameStarted:
            # check game state
            left_time = self.roundEndData - now
            timer_value = left_time.total_seconds()
            self.left_time = int(timer_value)
            if timer_value <= 0:
                self.gameStarted = False
                self.state = 'stop'
                timer_value = 0
        else:
            timer_value = 0
        return timer_value


class TerminalMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.Integer, db.ForeignKey('game.id'))
    time = db.Column(db.DateTime)
    author = db.Column(db.String(100), index=True)
    text = db.Column(db.String(200), index=True)
    answer = db.Column(db.String(200), index=True)

    def __repr__(self):
        return '<Post {}>'.format(self.text)
