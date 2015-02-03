from flask import Flask, request, render_template,send_file
import gevent
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from flask.ext.sqlalchemy import SQLAlchemy
from socketio import packet
import json


class OpponentDisconnectedError(Exception):
    pass

class NoOpponentFoundException(Exception):
    pass

class GameNamespace(BaseNamespace):
    def initialize(self):
        opponent_sessid = self.find_opponent()
        self.session['ready'] = False
        self.session['turn'] = 0
        if opponent_sessid:
            self.session['opponent'] = opponent_sessid
            self.emit('opponent_connected', opponent_sessid) 
            self.notify_opponent('opponent_connected', self.socket.sessid)
        else:
            self.emit('wait', 'Please wait')
        self.spawn(self.check_opponent)

    def recv_connect(self):
        print "%s Connected" % self.socket.sessid

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
        print 'Guess' + data
        self.emit('guess_response', '3B 3C')
        self.emit_opponent('opponent_guess', data)
        self.emit_opponent('turn', '')
        opponent = self.get_opponent()
        opponent.session['turn'] = 1
        self.session['turn'] = 0

    def guess_response(self, guess):
        opponent = self.get_opponent()
        opponent_num = opponent['num']
        return

    def on_num(self, data):
        self.session['num'] = data
        self.session['ready'] = True
        if self.opponent_ready():
            self.emit('turn', '')
            self.session['turn'] = 1
        print 'Num' + data

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

