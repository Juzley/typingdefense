"""Module containing the different enemies that appear in the game."""
from typingdefense.phrase import Phrase


class Enemy(object):
    def __init__(self, app, cam, origin):
        self.origin = origin
        self.phrase = Phrase(app, cam, "PHRASE")

    def draw(self):
        self.phrase.draw(self.origin)
