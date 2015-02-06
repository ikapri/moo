from models import Game
import gevent

games = []

def find_game_to_join():
        """
        Find a game to join or ele start a new game
        and wait for someone else to join
        """
        for g in games:
            if g.game_can_be_joined():
                return g
        g = Game()
        games.append(g)
        return g

def remove_game(game):
    print "Removing Game %s " % game
    games.remove(game)

def game_watcher():
    while True:
        temp = []
        for g in games:
            if g.is_disconnected():
                print "Disconnected"
                g.notify_disconnection()
                temp.append(g)
        for t in temp:
            remove_game(t)
        gevent.sleep(1)

def spawn_watcher():
    gevent.spawn(game_watcher)
