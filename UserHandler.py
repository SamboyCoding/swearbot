import discord
import wave
import time
import os
import speech_recognition as sr
from Swears import swears
from NaughtyList import NaughtyList


class UserHandler:
    vc_channel_id = 706802399158730792

    def __init__(self, user: discord.Member, base_dir: str):
        guild: discord.Guild = user.guild
        self.guild = guild
        self.user = user
        self.base_path = base_dir + str(user.id)
        self.consecutive_silence_count = 1
        self.start_time = 0
        self.buffer = bytes(3840)
        self.r = sr.Recognizer()
        # print("Initialized new user handler for", user, "that logs to file", self.base_path)

    def receive_audio(self, pcm_data: bytes):
        # print("Got", len(pcm_data), "bytes audio data for", self.user, "in", self.guild.name)
        if self.consecutive_silence_count > 0:
            self.consecutive_silence_count = 0
            self.start_time = time.time()
        self.buffer += pcm_data

    async def receive_silence(self):
        self.consecutive_silence_count += 1
        if self.consecutive_silence_count == 15:
            # print("Received 15 silence packets for", self.user, "assuming they're done talking and flushing",
            #       len(self.buffer), "bytes to file")
            self.buffer += bytes(3840)  # Add some padding
            path = self.base_path + "_" + str(self.start_time) + ".wav"
            with wave.open(path, "wb") as f:
                f.setnchannels(discord.opus.Decoder.CHANNELS)
                f.setsampwidth(discord.opus.Decoder.SAMPLE_SIZE // discord.opus.Decoder.CHANNELS)
                f.setframerate(discord.opus.Decoder.SAMPLING_RATE)
                f.writeframes(self.buffer)

            # print("Wrote to file:", path)
            self.buffer = bytes(3840)
            await self.recognise(path)

    async def recognise(self, path: str):
        with sr.AudioFile(path) as f:
            audio = self.r.listen(f)
            try:
                response_sentence: str = self.r.recognize_google(audio, language="en-GB")

                result = ""
                swear_count = 0
                for word in response_sentence.split(" "):
                    key = word.lower()
                    if key in swears:
                        result += "**" + swears[key] + "**" + " "
                        swear_count += 1
                    elif "*" in key:
                        result += key.replace("*", "\\*") + " "
                    else:
                        result += word + " "
                # endfor

                guild: discord.Guild = self.user.guild
                channel: discord.TextChannel = guild.get_channel(UserHandler.vc_channel_id)

                naughty_list: NaughtyList = NaughtyList.instance
                score = naughty_list.get_user_score(self.user)
                score += swear_count
                naughty_list.set_user_score(self.user, score)

                print(self.user.display_name, "said {}".format(response_sentence))
                await channel.send(self.user.display_name + ": {}".format(result))
            except sr.UnknownValueError:
                print("No idea what was said by", self.user)
            except sr.RequestError as e:
                print("Failed to reach GSR:", e)
        # endwith
        os.remove(path)
