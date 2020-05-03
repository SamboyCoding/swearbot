import discord, os
import speech_recognition as sr


# Speech recognition API stuffs: https://github.com/Uberi/speech_recognition/blob/master/speech_recognition/__main__.py

class BotClient(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        print("Connecting...")
        self.r = sr.Recognizer()

    async def on_ready(self):
        print("Logged on as", self.user)

    # enddef

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if message.content == "ping":
            await message.channel.send("pong")
        # endif
    # enddef


# endclass

if __name__ == '__main__':
    client = BotClient()
    client.run(os.getenv("DISCORD_TOKEN"))
