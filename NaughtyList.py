import sqlite3
import discord
from typing import List, Tuple


class NaughtyList:
    instance = None

    def __init__(self):
        print("Connecting to local database file naughty_list.sqlite...")
        self.db = sqlite3.connect("naughty_list.sqlite")
        self.db.execute("CREATE TABLE IF NOT EXISTS swear_count (id INTEGER PRIMARY KEY, count INTEGER)")
        print("Ready.")

    def create_user(self, member: discord.Member):
        self.db.execute("INSERT INTO swear_count(id, count) VALUES (?, ?)", [member.id, 0])
        self.db.commit()

    def set_user_score(self, member: discord.Member, score: int):
        id: int = member.id
        self.db.execute("UPDATE swear_count SET count = ? WHERE id = ?", [score, id])
        self.db.commit()

    def get_user_score(self, member: discord.Member) -> int:
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
        cur = self.db.cursor()
        cur.execute("SELECT * FROM swear_count ORDER BY count DESC LIMIT 10")
        results: List[Tuple[int]] = cur.fetchall()
        return results

