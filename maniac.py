import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
from collections import deque

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    queues = {}
    voice_clients = {}
    yt_dl_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25" -f opus'}

    async def play_next(guild_id, text_channel):
        if guild_id in queues and queues[guild_id]:
            song, title = queues[guild_id].popleft()
            voice_client = voice_clients[guild_id]
            player = discord.FFmpegOpusAudio(song, **ffmpeg_options)
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild_id, text_channel), client.loop))
            await text_channel.send(f"Reproduciendo: {title}")
        else:
                await asyncio.sleep(5)

    @client.event
    async def on_ready():
        print(f'{client.user} is now jamming')

    @client.event
    async def on_message(message):
        command = message.content.lower()

        if command.startswith("!p "):
            try:
                guild_id = message.guild.id
                if guild_id not in voice_clients or not voice_clients[guild_id].is_connected():
                    voice_client = await message.author.voice.channel.connect()
                    voice_clients[guild_id] = voice_client
                    queues[guild_id] = deque()
                else:
                    voice_client = voice_clients[guild_id]

                query = message.content[len("!p "):]

                if "youtube.com/watch" in query or "youtu.be/" in query:
                    url = query
                else:
                    url = f"ytsearch:{query}"

                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

                if 'entries' in data:
                    song = data['entries'][0]['url']
                    title = data['entries'][0]['title']
                else:
                    song = data['url']
                    title = data.get('title', 'Unknown Title')

                queues[guild_id].append((song, title))

                if not voice_client.is_playing():
                    await play_next(guild_id, message.channel)

                await message.channel.send(f"Agregado a la cola: {title}")
            except Exception as e:
                print(e)

        if command.startswith("!pause"):
            try:
                voice_clients[message.guild.id].pause()
            except Exception as e:
                print(e)

        if command.startswith("!resume"):
            try:
                voice_clients[message.guild.id].resume()
            except Exception as e:
                print(e)

        if command.startswith("!s"):
            try:
                voice_clients[message.guild.id].stop()
                await play_next(message.guild.id, message.channel)
            except Exception as e:
                print(e)

    client.run(TOKEN)

run_bot()
