import weakref
import uuid

GAME_WAITING = 0
GAME_STARTED = 1
GAME_FINISHED = 2

class Game():
    def __del__(self):
        print "GAME is being deleted"

    def __init__(self, p1=None, p2=None):
        self.id = str(uuid.uuid4())
        print "Creating Game : %s" % self
        self.p1 = p1
        self.p2 = p2
        if p1 is None or p2 is None:
            self.state = GAME_WAITING
        else:
            self.state = GAME_STARTED

    def find_bulls_cows(self, number, guess):
        res = {'B':0 ,'C':0}
        for index,num in enumerate(guess):
            if num in number:
                if number[index] == num:
                    res['B']+=1
                else:
                    res['C']+=1
        return res

    def add_player(self, player):
        print "Adding Player: %s to Game %s " % (player.id, self)
        if self.p1 is None:
            self.p1 = player
            player.emit('wait','Searching for opponent..Please wait')
        elif self.p2 is None:
            self.p2 = player
            player.emit('opponent_connected','Connected')
            self.p1.emit('opponent_connected', 'Connected')
            self.state = GAME_STARTED
        else:
            raise Exception('Game Already has two players')

    def game_init(self):
        print "Game Init"
        pass

    def start_game(self):
        print "Start Game"
        self.p1.emit('turn')

    def restart_game(self):
        pass

    def play_turn(self, player, guess):
        if player is self.p1:
            opp = self.p2
        elif player is self.p2:
            opp = self.p1
        else:
            raise Exception("Invalid Player")
        resp = self.find_bulls_cows(opp.number, guess)
        if not self.is_won(resp, guess):
            player.emit('guess_response', resp)
            opp.emit('opponent_guess', resp)
            opp.emit('turn', '')
        else:
            player.emit('won', guess)
            opp.emit('loss', guess)
            self.state = GAME_FINISHED

    def is_won(self, resp, guess):
        return resp.get('B') == len(guess)

    def receive_number(self, player, number):
        if player is self.p1:
            opp = self.p2
        elif player is self.p2:
            opp = self.p1
        else:
            raise Exception("Invalid Player")
        player.set_number(number)
        if opp.is_ready():
            self.start_game()

    def game_can_be_joined(self):
        return self.state == GAME_WAITING

    def is_disconnected(self):
        if self.state == GAME_WAITING:
            return not self.p1.is_currently_connected()
        return not (self.p1.is_currently_connected() and self.p2.is_currently_connected())

    def notify_disconnection(self):
        if self.p1:
            self.p1.emit('opponent_disconnected')
        if self.p2:
            self.p2.emit('opponent_disconnected')

    def __repr__(self):
        return self.id


class Player():
    def __init__(self, ns, number=None):
        self.number = number 
        self._ns = weakref.proxy(ns)
        self.id = ns.socket.sessid

    def is_ready(self):
        return self.number is not None

    def set_number(self, number):
        self.number = number

    def emit(self, event, *args):
        try:
            self._ns.emit(event, args)
        except ReferenceError as e:
            print str(e)
            return
        return True

    def is_currently_connected(self):
        try:
            return self._ns.socket.connected
        except ReferenceError:
            return False

    def __del__(self):
        print "Player %s is being deleted" % self.id
