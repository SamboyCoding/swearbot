import discord
import os
import shutil
from typing import Dict
from UserHandler import UserHandler
import asyncio


class SpeechRecognisingSink(discord.AudioSink):
    # TODO: Rework this to not extend wavesink - it is not flexible enough.
    # TODO: Then we basically have to decide on an approach - do we take x silence packets as a word break, divide words
    # TODO: into the packet.sequence they began on, and then run analysis on words? That might work, or can we try to do
    # TODO: whole sentences at once with longer pauses? Either way, save to unique files, run detection, then del.
    # TODO: However, the actual receiving part works fine ;P
    def __init__(self, guild: discord.Guild):
        super().__init__()

        guild_path: str = "./user_data/" + str(guild.id) + "/"

        if os.path.isdir(guild_path):
            shutil.rmtree(guild_path)

        os.makedirs(guild_path, exist_ok=True)

        user_handlers: Dict[int, UserHandler] = {}
        self.user_handlers = user_handlers
        self.loop = asyncio.get_event_loop()

        print("Now listening to", guild.name)
        self.guild = guild
        self.guild_path = guild_path

    def write(self, data: discord.reader.VoiceData):
        # loop: asyncio.AbstractEventLoop
        # try:
        #     loop = asyncio.get_event_loop()
        # except RuntimeError:
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)

        member: discord.Member = data.user
        pcm: bytes = data.data

        if member.bot:
            return

        if member.id not in self.user_handlers:
            self.user_handlers[member.id] = UserHandler(member, self.guild_path)

        user_handler = self.user_handlers[member.id]

        if isinstance(data.packet, discord.reader.SilencePacket):
            asyncio.run_coroutine_threadsafe(user_handler.receive_silence(), self.loop)
            # future = asyncio.ensure_future(user_handler.receive_silence())
            # loop.run_until_complete(future)
        else:
            user_handler.receive_audio(pcm)
