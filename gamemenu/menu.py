"""Menu class, represents a menu system made up of a number of screens."""


class Menu(object):

    """Menu class.

    Manages a number of menu screens and coordinates moving between them.
    """

    def __init__(self, start_screen):
        """Initialize a menu."""
        self._menu_stack = []
        self.reset(start_screen)

    def draw(self):
        """Draw the menu."""
        self._menu_stack[-1].Draw()

    def reset(self, screen):
        """Reset the menu.

        This discards the current menu stack and starts again at the given
        screen.
        """
        self._menu_stack = [screen]

    def navigate_forward(self, screen):
        """Move to a new screen.

        The current screen is kept on the stack so we can go back to it.
        """
        self._menu_stack.append(screen)

    def navigate_back(self):
        """Move to the previous screen."""
        self._menu_stack.pop()
