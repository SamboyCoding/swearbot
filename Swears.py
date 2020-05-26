import sqlite3
from typing import List, Tuple


swears = {
    # Google do be making up words though
    "motherfuker": "motherfucker",
    "f******": "fucking",
    "fucking": "fucking",
    "f***": "fuck",
    # ???
    "fuk": "fuck",
    "fuck": "fuck",
    "feck": "feck",  # Simply because I type this too much
    "ffs": "ffs",
    "s***": "shit",
    "shit": "shit",
    # Seriously what
    "shity": "shitty",
    "shitty": "shitty",
    "crap": "crap",
    "b****": "bitch",
    "bitch": "bitch",
    "bollocks": "bollocks",
    "b*******": "bollocks",
    "cock": "cock",
    "dick": "dick",
    "bastard": "bastard",
    # Thanks ty
    "boobies": "boobies",
    "tits": "tits",
    "cunt": "cunt",
    "c***": "cunt",
    # Again, ty
    "heck": "heck",
    "darn": "darn",
    "piss": "piss",
    "ass": "ass",
    "hell": "hell",
    "damn": "damn",
    "dammit": "dammit",
    "damnit": "damnit",  # Because mallord can't spell lmao
    "wtf": "wtf",
    # Mallord found some loopholes so I'll have to close them
    "shithead": "shithead",
    "shitshow": "shitshow",
    "shitfucker": "shitfucker",  # What does this actually mean? TODO: Ask mallord.
    "wank": "wank",
    "pillock": "pillock"
}


class Swears:
    instance = None

    def __init__(self):
        """Connect to swear_words database. Create a new database if it does not exist."""
        print("Connecting to local database file swear_words.sqlite...")
        self.db = sqlite3.connect("swears.sqlite")
        self.db.execute("CREATE TABLE IF NOT EXISTS swear_words (id STRING PRIMARY KEY, equivalence STRING)")

        # This makes sure the database is full on first execution
        cur = self.db.cursor()
        cur.execute("SELECT id FROM swear_words")
        results: List[Tuple[str]] = cur.fetchall()
        if len(results) < 1:
            print("Database empty! Updating with current swears...")
            for swear_word, equivalence in swears.items():
                self.db.execute("INSERT INTO swear_words (?, ?)", [swear_word, equivalence])
            self.db.commit()
            print("Database updated!")

        print("Ready.")

    def add_swear_word(self, swear_word: str, equivalence: str):
        """Add a new swear word and its equivalent spelling to the database"""
        self.db.execute("INSERT INTO swear_words (?, ?)", [swear_word, equivalence])
        self.db.commit()

    def get_swear_words(self) -> List[str]:
        """Return all the swear word keys stored in the database as a list"""
        # TODO Check over this code section
        cur = self.db.cursor()
        cur.execute("SELECT id FROM swear_words")

        results: List[Tuple[str]] = cur.fetchall()
        if len(results) < 1:
            return [" "]  # This means no swear words are stored in the database

        keys: List[str] = [row[0] for row in results]  # Returns the first element in each row, ie. the keys
        return keys

    def get_equivalent(self, swear_word: str) -> str:
        """Return a given swear word equivalent. Create a new user if they do not exist."""
        cur = self.db.cursor()
        cur.execute("SELECT equivalence FROM swear_words WHERE id = ?", [swear_word])

        results: List[Tuple[str]] = cur.fetchall()
        if len(results) < 1:  # This should never execute as a check should be made before get_equivalence is run
            return swear_word  # In any case return the word given (there is no equivalence)

        row = results[0]
        return row[0]