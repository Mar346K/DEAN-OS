from enum import Enum

class Suit(Enum):
    HEARTS = 'Hearts'
    DIAMONDS = 'Diamonds'
    CLUBS = 'Clubs'
    SPADES = 'Spades'

class Card:
    def __init__(self, suit: Suit, value: int):
        self.suit = suit
        self.value = value
