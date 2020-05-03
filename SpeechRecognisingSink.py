import discord
import os


class SpeechRecognisingSink(discord.WaveSink):
    # TODO: Rework this to not extend wavesink - it is not flexible enough.
    # TODO: Then we basically have to decide on an approach - do we take x silence packets as a word break, divide words
    # TODO: into the packet.sequence they began on, and then run analysis on words? That might work, or can we try to do
    # TODO: whole sentences at once with longer pauses? Either way, save to unique files, run detection, then del.
    # TODO: However, the actual receiving part works fine ;P
    def __init__(self, guild: discord.Guild):
        guild_path = "./user_data/" + str(guild.id) + "/"
        os.makedirs(guild_path, exist_ok=True)

        super().__init__(guild_path + "/out.wav")
        print("Now listening to", guild.name)
        self.guild = guild

    def write(self, data: discord.reader.VoiceData):
        super().write(data)
        if isinstance(data.packet, discord.reader.SilencePacket):
            print("Got silence for", data.user)  # This works correctly - can we use it for message detection?
        else:
            print("Got", len(data.data), "bytes audio data for", data.user, "in", self.guild.name, "packet is",
                  data.packet)
