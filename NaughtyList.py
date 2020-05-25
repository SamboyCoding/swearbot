import sqlite3
import discord
from typing import List, Tuple


class NaughtyList:
    instance = None

    def __init__(self):
        """Connect to naughty_list database. Create a new database if it does not exist."""
        print("Connecting to local database file naughty_list.sqlite...")
        self.db = sqlite3.connect("naughty_list.sqlite")
        self.db.execute("CREATE TABLE IF NOT EXISTS swear_count (id INTEGER PRIMARY KEY, count INTEGER)")
        print("Ready.")

    def create_user(self, member: discord.Member):
        """Add new user, with no swears, into database."""
        self.db.execute("INSERT INTO swear_count(id, count) VALUES (?, ?)", [member.id, 0])
        self.db.commit()

    def set_user_score(self, member: discord.Member, score: int):
        """Update a given discord members swear count."""
        id: int = member.id
        self.db.execute("UPDATE swear_count SET count = ? WHERE id = ?", [score, id])
        self.db.commit()

    def get_user_score(self, member: discord.Member) -> int:
        """Return a given user's swear count. Create a new user if they do not exist."""
        id: int = member.id
        cur = self.db.cursor()
        cur.execute("SELECT count FROM swear_count WHERE id = ?", [id])

        results: List[Tuple[int]] = cur.fetchall()
        if len(results) < 1:
            self.create_user(member)
            return 0

        row = results[0]
        return row[0]

    def get_top_10(self):
        """Return the ten highest scored members."""
        cur = self.db.cursor()
        cur.execute("SELECT * FROM swear_count ORDER BY count DESC LIMIT 10")
        results: List[Tuple[int, int]] = cur.fetchall()
        return results

