from typing import Tuple, Optional, List, Coroutine
import math
import discord
import os
import speech_recognition as sr

from Constants import Constants
from SpeechRecognisingSink import SpeechRecognisingSink
from NaughtyList import NaughtyList
from Swears import swears


def better_round(value: float, decimals: int):
    decimal_coeff = 10 ** decimals
    return math.floor(value * decimal_coeff + 0.5) / decimal_coeff


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
            print("Opus loaded.")
        for guild in self.guilds:
            await self.work_out_which_vc_to_join(guild)

    # enddef

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content: str = message.content

        if content == "--jar":
            score = NaughtyList.instance.get_user_score(message.author)
            await message.channel.send(
                "You've sworn " + str(score) + " times, and therefore owe the swear jar approximately £" +
                str(better_round(score * 0.069, 2))
            )
        elif content == "--top":
            results = NaughtyList.instance.get_top_10()
            text = "**Naughtiest Users:**\n```"
            total_pool = 0.0
            guild: discord.Guild = message.guild
            for (uid, count) in results:
                username = guild.get_member(uid).display_name
                owes = count * 0.069
                text += username + " - " + str(count) + " - owes approx £" + str(better_round(owes, 2)) + "\n"
                total_pool += owes
            text += "```\n"
            text += "**The total pool therefore sits at about £" + str(better_round(total_pool, 2)) + "**"
            await message.channel.send(text)
        elif content.startswith("--addswears") and len(
                content.split(" ")) > 2 and message.author.id == 102450956045668352:  # Thas me
            if len(message.mentions) > 0:
                target: discord.Member = message.mentions[0]
                amount = int(content.split(" ")[2])
                initial = NaughtyList.instance.get_user_score(target)
                new = initial + amount
                NaughtyList.instance.set_user_score(target, new)
                await message.channel.send(
                    "Bumped " + target.mention + "'s score from " + str(initial) + " to " + str(new) + ". Tut-tut.")

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

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        if member.bot:
            return

        old_vc = await self.get_vc_for_guild(member.guild)
        new_channel = await self.work_out_which_vc_to_join(member.guild)
        if new_channel is None:
            return

        old_vc: discord.VoiceClient = old_vc

        guild: discord.Guild = member.guild
        logging_channel: discord.TextChannel = guild.get_channel(Constants.vc_channel_id)

        if old_vc is None or old_vc.channel != new_channel:
            # If WE have moved or joined a channel as a result of this update
            if before.channel == new_channel and after.channel is None:
                # User left channel and we moved to a more populated one (or left all of them)
                if new_channel is not None:
                    await logging_channel.send(
                        "**===" + member.display_name + " left " + before.channel.name + " so I moved to " + new_channel.name + "===**")
                else:
                    await logging_channel.send(
                        "**===" + member.display_name + " left " + before.channel.name + " so I left it too, as it's now empty===**")
            elif before.channel is None and after.channel == new_channel:
                # User joined our new channel - it's their fault we joined
                await logging_channel.send(
                    "**===" + member.display_name + " joined " + after.channel.name + " so I joined them.")
            elif before.channel is not None and after.channel == new_channel:
                # They moved from one to another so we did too
                await logging_channel.send(
                    "**===" + member.display_name + " moved from " + before.channel.name + " to " + after.channel.name
                    + ", making it the new most populous channel, so I followed them.===**"
                )
        elif before.channel != new_channel and after.channel == new_channel:
            # If someone joined our channel
            await logging_channel.send("**-" + member.display_name + " joined channel " + new_channel.name + "-**")
        elif before.channel == new_channel and after.channel != new_channel:
            # Someone left our channel
            await logging_channel.send("**-" + member.display_name + " left channel " + new_channel.name + "-**")


    async def leave_vc_for_guild(self, guild: discord.Guild):
        vc = await self.get_vc_for_guild(guild)
        if vc:
            await vc.disconnect()


    async def get_vc_for_guild(self, guild: discord.Guild) -> Optional[discord.VoiceClient]:
        for voice_client in self.voice_clients:
            if voice_client.channel.guild.id == guild.id:
                return voice_client
        return None


    async def work_out_which_vc_to_join(self, guild: discord.Guild) -> Optional[discord.VoiceChannel]:
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
            return None

        if vc and vc.channel.id == max_tuple[1].id:
            # already in the right channel
            await self.update_listeners(guild)
            return max_tuple[1]
        elif vc:
            await vc.disconnect()

        await max_tuple[1].connect()
        await self.update_listeners(guild)
        return max_tuple[1]


    async def update_listeners(self, guild: discord.Guild):
        vc = await self.get_vc_for_guild(guild)
        channel: discord.VoiceChannel = vc.channel

        if not vc.is_listening():
            vc.listen(SpeechRecognisingSink(guild))


# endclass

if __name__ == '__main__':
    client = BotClient()
    client.run(os.getenv("DISCORD_TOKEN"))
