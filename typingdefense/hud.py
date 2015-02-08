from typingdefense.text import Text

class Hud(object):
    def __init__(self, app):
        font = app.resources.load_font("hudfont.fnt")
        self._test_text = Text(app, font, "TEST!", 400, 300, 32,
                               Text.Align.center)

    def draw(self):
        self._test_text.draw()
