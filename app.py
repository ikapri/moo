from flask import Flask, request, render_template
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
import game_server as gs
from models import  Player

gs.spawn_watcher()

class GameNamespace(BaseNamespace):
    def __del__(self):
        print "Deleting NS %s" % self.socket.sessid

    def initialize(self):
        p = Player(self)
        self.player = p 
        game = gs.find_game_to_join()
        game.add_player(p)
        self.game = game

    def recv_connect(self):
        print "%s Connected" % self.socket.sessid

    def on_guess(self, data):
        self.game.play_turn(self.player, data)

    def on_num(self, data):
        self.game.receive_number(self.player, data)
    
    def on_ping(self, data):
        print "PING"



app = Flask(__name__)

@app.route('/socket.io/<path:path>')
def sock(path):
    socketio_manage(request.environ, {"/game": GameNamespace}, request)

@app.route('/play')
def home():
    print 'HOME'
    return render_template('index.html')

