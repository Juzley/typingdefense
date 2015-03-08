import random


class ConcatList(object):
    """A class for concatenating lists without copying the lists.

    This works using a list of references to the lists in the concatenation.
    Modifying the constituent lists will modify the ConcatList accordingly."""
    def __init__(self, *args):
        self._lists = []
        for a in args:
            self._lists.append(a)

    def _add(self, l):
        if type(l) is not list:
            raise TypeError('Can only add lists to ConcatList')
        if l not in self._lists:
            self._lists.append(l)

    def __len__(self):
        length = 0
        for l in self._lists:
            length += len(l)
        return (length)

    def __iter__(self):
        for l in self._lists:
            for i in l:
                yield i

    def __getitem__(self, index):
        for l in self._lists:
            if index < len(l):
                return l[index]
            else:
                index -= len(l)
        raise IndexError('ConcatList index out of range')

    def __iadd__(self, other):
        self._add(other)
        return self


class PhraseBook(object):
    SINGLE_PHRASE = range(1, 2)
    SHORT_PHRASE = range(2, 5)
    MED_PHRASE = range(5, 8)
    LONG_PHRASE = range(8, 12)
    HUGE_PHRASE = range(12, 20)
    def __init__(self, filename):
        self._available_letters = set()

        # Words are stored in the _phrases member according to their length and
        # start character.
        # This is a dictionary, keyed on a range representing the length of
        # words in the corresponding item. Each item is a dictionary keyed on
        # the start character of words, where the corresponding item is a list
        # containing all the words of the given length and start character.
        self._phrases = {PhraseBook.SINGLE_PHRASE: {},
                         PhraseBook.SHORT_PHRASE: {},
                         PhraseBook.MED_PHRASE: {},
                         PhraseBook.LONG_PHRASE: {},
                         PhraseBook.HUGE_PHRASE: {}}
        with open(filename, mode='r', encoding='ascii', errors='ignore') as f:
            for line in [l.strip() for l in f]:
                self._add_word(line)

    def _add_word(self, word):
        if len(word) in PhraseBook.SINGLE_PHRASE:
            slot = self._phrases[PhraseBook.SINGLE_PHRASE]
        elif len(word) in PhraseBook.SHORT_PHRASE:
            slot = self._phrases[PhraseBook.SHORT_PHRASE]
        elif len(word) in PhraseBook.MED_PHRASE:
            slot = self._phrases[PhraseBook.MED_PHRASE]
        elif len(word) in PhraseBook.LONG_PHRASE:
            slot = self._phrases[PhraseBook.LONG_PHRASE]
        elif len(word) in PhraseBook.HUGE_PHRASE:
            slot = self._phrases[PhraseBook.HUGE_PHRASE]
        else:
            # Don't want to store words longer than the max phrase length
            return

        start = word[0]
        if start not in slot:
            slot[start] = []
        slot[start].append(word)
        self._available_letters.add(start)

    def get_word(self, length):
        words = ConcatList()
        for c in self._available_letters:
            if c in self._phrases[length]:
                words += self._phrases[length][c]

        word = random.choice(words)
        self._available_letters.remove(word[0])
        return word

    def get_phrase(self, length, count):
        if count > 1:
            raise NotImplementedError('TODO: Multi-word phrases')
        return self.get_word(length)

    def release_start_letter(self, letter):
        self._available_letters.add(letter)
