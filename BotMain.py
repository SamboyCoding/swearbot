from typing import Tuple, Optional, List, Coroutine
import math
import discord
import os
import speech_recognition as sr

from Constants import Constants
from SpeechRecognisingSink import SpeechRecognisingSink
from NaughtyList import NaughtyList
from Swears import Swears


def better_round(value: float, decimals: int):
    """Utilise math.floor to more accurately round numbers."""
    decimal_coeff = 10 ** decimals
    return math.floor(value * decimal_coeff + 0.5) / decimal_coeff


class BotClient(discord.Client):
    def __init__(self, **options):
        """Initialise a discord client; create a new recogniser and naughty list database instance."""
        super().__init__(**options)
        print("Initializing SR...")
        self.r = sr.Recognizer()
        NaughtyList.instance = NaughtyList()
        Swears.instance = Swears()
        print("Connecting to discord...")

    async def on_ready(self):
        """Login and start discord Opus if not already started. Join relevant discord voice channel."""
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
        """Carry out user commands and monitor text channels for swears by users.

        --jar: Posts the authors current swear count and money owed.
        --top: Posts the top ten server swearers.
        --addswears (exclusive to Sam): Adds swears to a specific user.
        profanic sentences are highlighted with the 'swear' emoji.
        """
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
                user: discord.Member = guild.get_member(uid)
                if user:
                    username = user.display_name
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
        elif content.startswith("--addswearword") and len(
                content.split(" ")) > 1 and (message.author.id == 102450956045668352 or
                                             message.author.id == 562295765263712262):
            contents = content.split(" ")
            if len(contents) == 3:
                swear_word: str = contents[1]
                equivalence: str = contents[2]
                Swears.instance.add_swear_word(swear_word, equivalence)
                await message.channel.send("Added " + swear_word + " to the database. Don't try to be sneaky.")
            elif len(contents) == 2:
                swear_word: str = contents[1]
                Swears.instance.add_swear_word(swear_word, swear_word)
                await message.channel.send("Added " + swear_word + " to the database. Don't try to be sneaky.")

        swear_count = 0
        for word in content.split(" "):
            key = word.lower().strip("!?.,")
            if key in Swears.instance.get_swear_words():
                swear_count += 1
        # endfor

        if swear_count > 0:
            original = NaughtyList.instance.get_user_score(message.author)
            new = original + swear_count
            NaughtyList.instance.set_user_score(message.author, new)
            await message.add_reaction("🤬")

    # enddef

    async def on_voice_state_update(self, member: discord.Member, their_before: discord.VoiceState,
                                    their_after: discord.VoiceState):
        """Update the bots channel based on the popularity of guild voice channels.

        Posts messages in the vc_log guild channel to alert when it moves channel along with it's reason.
        It also notifies users when a new user joins or moves voice channel."""
        if member.bot:
            return

        old_vc = await self.get_vc_for_guild(member.guild)
        our_after = await self.work_out_which_vc_to_join(member.guild)

        old_vc: discord.VoiceClient = old_vc
        our_before: Optional[discord.VoiceChannel] = None
        if old_vc is not None:
            our_before = old_vc.channel

        guild: discord.Guild = member.guild
        logging_channel: discord.TextChannel = guild.get_channel(Constants.vc_channel_id)

        if old_vc is None or our_before != our_after:
            # If WE have moved or joined a channel as a result of this update
            if their_before.channel == our_before and their_after.channel is None:
                # User left channel and we moved to a more populated one (or left all of them)
                if our_after is not None:
                    await logging_channel.send(
                        "**===" + member.display_name + " left " + their_before.channel.name + " so I moved to " + our_after.name + "===**")
                else:
                    await logging_channel.send(
                        "**===" + member.display_name + " left " + their_before.channel.name + " so I left it too, as it's now empty===**")
            elif their_before.channel is None and their_after.channel == our_after:
                # User joined our new channel - it's their fault we joined
                await logging_channel.send(
                    "**===" + member.display_name + " joined " + their_after.channel.name + " so I joined them.===**")
            elif their_before.channel is not None and their_after.channel == our_after:
                # They moved from one to another so we did too
                await logging_channel.send(
                    "**===" + member.display_name + " moved from " + their_before.channel.name + " to " + their_after.channel.name
                    + ", making it the new most populous channel, so I followed them.===**"
                )
        elif their_before.channel != our_after and their_after.channel == our_after:
            # If someone joined our channel
            await logging_channel.send("**-" + member.display_name + " joined channel " + our_after.name + "-**")
        elif their_before.channel == our_after and their_after.channel != our_after:
            # Someone left our channel
            await logging_channel.send("**-" + member.display_name + " left channel " + our_after.name + "-**")


    async def leave_vc_for_guild(self, guild: discord.Guild):
        """Find current voice channel then disconnect from it."""
        vc = await self.get_vc_for_guild(guild)
        if vc:
            await vc.disconnect()


    async def get_vc_for_guild(self, guild: discord.Guild) -> Optional[discord.VoiceClient]:
        """Return current voice channel."""
        # Ngl not entirely sure if that is it but seems right from context
        for voice_client in self.voice_clients:
            if voice_client.channel.guild.id == guild.id:
                return voice_client
        return None


    async def work_out_which_vc_to_join(self, guild: discord.Guild) -> Optional[discord.VoiceChannel]:
        """Loop over all voice channels and connect to the channel with the most users.

        Don't disconnect and reconnect if already in the right channel, rather update the audio recognition."""
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
        """If the bot is not listening to current voice channel start listening."""
        vc = await self.get_vc_for_guild(guild)
        channel: discord.VoiceChannel = vc.channel

        if not vc.is_listening():
            vc.listen(SpeechRecognisingSink(guild))


# endclass

if __name__ == '__main__':
    client = BotClient()
    client.run(os.getenv("DISCORD_TOKEN"))
