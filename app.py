from flask import Flask, request, render_template
import gevent
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from flask.ext.sqlalchemy import SQLAlchemy
import json


class Player():
    def __init__(self, ns, number=None):
        self.number = number 
        self._ns = ns
        self.id = ns.socket.sessid
    
    def is_ready(self):
        return self.number is not None

    def set_number(self, number):
        self.number = number

    def emit(self, event, *args):
        self._ns.emit(event, args)

class Game():
    def __init__(self, p1=None, p2=None):
        self.p1 = p1
        self.p2 = p2
        self.started = False

    def add_player(self, player):
        print "Adding Player: ",
        print player.id
        if self.p1 is None:
            self.p1 = player
            player.emit('PWAIT',' please wait')
        elif self.p2 is None:
            self.p2 = player
            player.emit('connected','Connected')
            self.p1.emit('connected', 'Connected')
            self.started = True
        else:
            raise Exception('Game Already has two players')

    def game_init(self):
        print "Game Init"
        pass

    def start_game(self):
        print "Start Game"
        pass

    def restart_game(self):
        pass

    def play_turn(self, player, guess):
        print "Turn"
        player.emit('asd', 'teri turn hui')
        pass

class GameServer():
    def __init__(self):
        self.games = []

    def find_game_to_join(self):
        """
        Find a game to join or ele start a new game
        and wait for someone else to join
        """
        for g in self.games:
            if not g.started:
                return g
        g = Game()
        self.games.append(g)
        return g

    
gs = GameServer()
class OpponentDisconnectedError(Exception):
    pass

class NoOpponentFoundException(Exception):
    pass

class GameNamespace(BaseNamespace):
    def initialize(self):
        '''opponent_sessid = self.find_opponent()
        self.session['ready'] = False
        self.session['turn'] = 0
        if opponent_sessid:
            self.session['opponent'] = opponent_sessid
            self.emit('opponent_connected', opponent_sessid) 
            self.notify_opponent('opponent_connected', self.socket.sessid)
            self.session['player_type'] = 'P2'
            self.opponent = self.get_opponent()
        else:
            self.emit('wait', 'Please wait')
            self.session['player_type'] = 'P1'
        self.spawn(self.check_opponent)'''

    def recv_connect(self):
        print "%s Connected" % self.socket.sessid
        p=Player(self)
        self.player = p
        game=gs.find_game_to_join()
        game.add_player(p)
        self.game = game

    def on_ping(self, data):
        pass

    def check_opponent(self):
        while True:
            if not self.session.get('opponent'):
                gevent.sleep(1)
                continue
            if not self.opponent_connected():
                self.emit('opponent_disconnected','')
                break
            self.notify_opponent('ping','PING')
            gevent.sleep(1)

    def on_opponent_connected(self, data):
        self.emit('opponent_connected', '')
        self.session['opponent'] = data


    def on_guess(self, data):
        '''resp = self.guess_response(data)
        if resp['B'] == len(data):
            self.emit('win', data)
            self.notify_opponent('loss', data)
        else:
            self.session['turn'] = 0
            self.emit('guess_response', resp)
            self.notify_opponent('opponent_guess', data)'''
        self.game.play_turn(self.player, data)

    def on_loss(self, data):
        self.emit('loss', data)

    def on_opponent_guess(self, data):
        self.session['turn'] = 1
        self.emit('turn', '')
        self.emit('opponent_guess', data)

    def guess_response(self, guess):
        opponent = self.get_opponent()
        opponent_num = opponent.session['num']
        result = self.find_bulls_cows(opponent_num, guess)
        return result

    def find_bulls_cows(self, number, guess):
        res = {'B':0 ,'C':0}
        for index,num in enumerate(guess):
            if num in number:
                if number[index] == num:
                    res['B']+=1
                else:
                    res['C']+=1
        return res

    def on_num(self, data):
        self.player.set_number = data
        '''self.session['num'] = data
        self.session['ready'] = True
        if self.opponent_ready():
            if self.session['player_type'] == 'P1':
                self.emit('turn', '')
                self.session['turn'] = 1
            else:
                self.notify_opponent('turn', '')
                opponent = self.get_opponent()
                opponent.session['turn'] = 1'''

    def opponent_ready(self):
        opponent = self.get_opponent()
        return opponent.session.get('ready')

    def opponent_connected(self):
        return self.session.get('opponent') in self.socket.server.sockets

    def notify_opponent(self, event, *args):
        msg_str = '5::%s:%s'
        d = {'args': args, 'name': event}
        msg_str = msg_str % (self.ns_name, json.dumps(d))
        opponent_socket = self.get_opponent()
        opponent_socket.put_server_msg(msg_str)

    def get_opponent(self):
        if self.session.get('opponent'):
            opponent_sessid = self.session['opponent']
            if self.opponent_connected():
                return self.socket.server.sockets[opponent_sessid]
            raise OpponentDisconnectedError 
        raise NoOpponentFoundException
        
    def find_opponent(self):
        for sessid,sock in self.socket.server.sockets.iteritems():
            if not sock is self.socket and not sock.session.get('opponent') and sock.connected:
                return sock.sessid



app = Flask(__name__)
db = SQLAlchemy(app)

@app.route('/socket.io/<path:path>')
def sock(path):
    socketio_manage(request.environ, {"/game": GameNamespace}, request)


@app.route('/game')
def game():
    print 'GAME'

@app.route('/play')
def home():
    print 'HOME'
    return render_template('index.html')

