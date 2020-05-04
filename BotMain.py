from typing import Tuple, Optional, List

import discord
import os
import speech_recognition as sr
from SpeechRecognisingSink import SpeechRecognisingSink
from NaughtyList import NaughtyList
from Swears import swears


# Speech recognition API stuffs: https://github.com/Uberi/speech_recognition/blob/master/speech_recognition/__main__.py

class BotClient(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        print("Initializing SR...")
        self.r = sr.Recognizer()
        NaughtyList.instance = NaughtyList()
        print("Connecting to discord...")

    async def on_ready(self):
        print("Logged on as", self.user)
        if not discord.opus.is_loaded():
            print("Opus has not yet been loaded, manually loading it...")
            if os.name == 'posix':
                discord.opus.load_opus("libopus.so.0")
            else:
                discord.opus.load_opus("libopus-0.x64.dll")
        for guild in self.guilds:
            await self.work_out_which_vc_to_join(guild)

    # enddef

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if message.content == "--jar":
            score = NaughtyList.instance.get_user_score(message.author)
            await message.channel.send("You've sworn " + str(score) + " times.")
        # endif

        content: str = message.content
        swear_count = 0
        for word in content.split(" "):
            key = word.lower().strip("!?.,")
            if key in swears:
                swear_count += 1
        # endfor

        if swear_count > 0:
            original = NaughtyList.instance.get_user_score(message.author)
            new = original + swear_count
            NaughtyList.instance.set_user_score(message.author, new)
            await message.add_reaction("🤬")

    # enddef

    async def on_voice_state_update(self, member: discord.Member, before, after):
        if member.bot:
            return

        await self.work_out_which_vc_to_join(member.guild)

    async def leave_vc_for_guild(self, guild: discord.Guild):
        vc = await self.get_vc_for_guild(guild)
        if vc:
            await vc.disconnect()

    async def get_vc_for_guild(self, guild: discord.Guild) -> Optional[discord.VoiceClient]:
        for voice_client in self.voice_clients:
            if voice_client.channel.guild.id == guild.id:
                return voice_client
        return None

    async def work_out_which_vc_to_join(self, guild: discord.Guild):
        max_tuple: Tuple[int, Optional[discord.VoiceChannel]] = (0, None)

        # Work out which vc has the most people in it
        vc = await self.get_vc_for_guild(guild)
        for channel in guild.voice_channels:
            members: List[discord.Member] = []

            for mem in channel.members:
                if not mem.bot:
                    members.append(mem)

            count = len(members)

            if count > max_tuple[0]:
                max_tuple = (count, channel)

        if max_tuple[0] == 0:
            # Nobody in any vc, leave all.
            await self.leave_vc_for_guild(guild)
            return

        if vc and vc.channel.id == max_tuple[1].id:
            # already in the right channel
            await self.update_listeners(guild)
            return
        elif vc:
            await vc.disconnect()

        await max_tuple[1].connect()
        await self.update_listeners(guild)

    async def update_listeners(self, guild: discord.Guild):
        vc = await self.get_vc_for_guild(guild)
        channel: discord.VoiceChannel = vc.channel

        if not vc.is_listening():
            vc.listen(SpeechRecognisingSink(guild))


# endclass

if __name__ == '__main__':
    client = BotClient()
    client.run(os.getenv("DISCORD_TOKEN"))
