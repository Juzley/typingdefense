"""Module containing the different enemies that appear in the game."""
from typingdefense.phrase import Phrase


class Enemy(object):
    def __init__(self, app, cam, origin):
        self.origin = origin
        self.phrase = Phrase(app, cam, "PHRASE")

    def draw(self):
        self.phrase.draw(self.origin)

    def on_text(self, c):
        self.phrase.on_type(c)

    def unlink(self):
        return self.phrase.complete

    def update(self, timer):
        pass
