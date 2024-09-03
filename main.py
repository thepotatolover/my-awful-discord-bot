import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from ollama import AsyncClient
import python_weather   
import os
import csv
import cpuinfo
import socket
import psutil
import platform
import datetime
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import re
import subprocess
import yt_dlp

username = ""
client_id = ''
client_secret = ''
redirect_uri = 'http://localhost:8080/callback'
bot_token = ""
sharex_server_token = ""
sharex_server_api = 'http://192.168.0.155:3000/api/upload'
bot_owner_id = 1118973285766533250

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(username=username, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope="user-read-currently-playing"))


bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.cities = []

async def weather_autocomplete(interaction: discord.Interaction, currently_typed_city: str):
    choices = []
    with open('owm_city_list.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file) 
        choices = [app_commands.Choice(name=(row['owm_city_name'].title()+', '+row['country_short']), value=(row['owm_city_name'].title()+','+row['country_short']))
                   for row in reader if row['owm_city_name'].lower().startswith(currently_typed_city.lower())][:24] #elif currently_typed_city
    return choices[:24]

async def models_complete(interaction: discord.Interaction, current_typed: str):
    choices = ['llama3', 'llama2-uncensored','codellama', 'phi']
    filtered_choices = [app_commands.Choice(name=choice, value=choice) for choice in choices if choice.startswith(current_typed)]
    return filtered_choices

def milliseconds_to_minutes_seconds(milliseconds):
    seconds = milliseconds / 1000

    if seconds > 59:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}:{int(remaining_seconds)}"
    else:
        return f"0:{int(seconds)}"


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name}")

async def getweather(city):
  async with python_weather.Client(unit=python_weather.METRIC) as client:
    weather = await client.get(city)
    return(weather.location, weather.country, weather.temperature, weather.feels_like, weather.wind_speed, weather.local_population, weather.humidity)


async def chat(input, model):
  message = {'role': 'system', 'content': 'You are an ai chatbot for a discord bot do not mention anything about a discord bot just be helpful, Always answer in under 1500 words, Always follow these rules', 'role': 'user', 'content': input}
  return(await AsyncClient().chat(model=model, messages=[message]))

def convert_nanoseconds(nanoseconds):
    total_seconds = nanoseconds / 1e9

    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    
    return minutes, seconds


@bot.tree.command(name='ai')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.autocomplete(model=models_complete)
async def mister_ai(ctx: discord.Interaction, model: str, input: str):
    embed = discord.Embed(title="Generating",colour=0x5b4fa6)
    await ctx.response.send_message(embed=embed)
    ai_reply = await chat(input=input, model=model)
    ai_msg = ai_reply['message']['content']
    ai_time = ai_reply['total_duration']
    minutes, seconds = convert_nanoseconds(ai_time)
    embed = discord.Embed(description=f"{ai_msg}",colour=0xcf25b1)

    embed.set_footer(text=f"Took {minutes} minutes and {seconds} seconds")
    await ctx.edit_original_response(embed=embed)

@bot.tree.command(name='nou')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def mister_no_u(ctx: discord.Interaction):
    await ctx.response.send_message(content='no u')

@bot.tree.command(name='weather', description='BUGGY!!!!')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.autocomplete(city=weather_autocomplete)
async def mister_wether(ctx: discord.Interaction, city: str):
    location, country, temp, feels_like, wind_speed, population, humidity = await getweather(city)
    embed = discord.Embed(title="Weather",
                      description=f"Location: {location}, {country}",
                      colour=0x00b0f4)
    embed.add_field(name="Temperature:",
                    value=f"{temp}°C",
                    inline=True)
    embed.add_field(name="Feels like:",
                    value=f"{feels_like}°C",
                    inline=True)
    embed.add_field(name="Wind Speed (MPH):",
                    value=f"{wind_speed}",
                    inline=False)
    if population:
        embed.add_field(name="Population:",
                        value=f"{population}",
                        inline=False)
    embed.add_field(name="Humidity:",
                    value=f"{humidity}%",
                    inline=False)

    await ctx.response.send_message(embed=embed)

class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180):
       super().__init__(timeout=timeout)
    @discord.ui.button(label="Neofetch", style=discord.ButtonStyle.green, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = subprocess.run(["fastfetch -l none --pipe"], shell=True, capture_output=True, text=True)
        embed = discord.Embed(title="Fastfetch",
                      description=f"```ansi\n{result.stdout.strip()}```")
        await interaction.response.edit_message(embed=embed, view=None)

@bot.tree.command(name='host-info', description='system info')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def mister_hosty_info(ctx: discord.Interaction):
    embed = discord.Embed(title="loadering",colour=0x5b4fa6)
    await ctx.response.send_message(embed=embed)
    pycpuinf = cpuinfo.get_cpu_info()
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    ram_usage = memory_info.percent
    if os.name == 'nt':
        windows_gpus = subprocess.run("wmic path win32_VideoController get name", shell=True, capture_output=True, text=True)
        gpu = windows_gpus.stdout[5:].strip()
    elif os.name == 'posix':
        linux_gpus = subprocess.run("fastfetch -l none --pipe | grep 'GPU'", shell=True, capture_output=True, text=True)
        gpu = linux_gpus.stdout[5:]
    else:
        gpu = "N/A"
    
    embed = discord.Embed(title="Status:",
                    colour=0x00b0f4,)
    embed.add_field(name="Bot Ping:",
                    value=f"`{round(bot.latency*1000)} ms`",
                    inline=True)
    embed.add_field(name="Local IP:",
                    value=f"`{local_ip}`",
                    inline=True)
    embed.add_field(name="Hostname:",
                    value=f"`{hostname}`",
                    inline=True)
    embed.add_field(name="OS:",
                    value=f"`{platform.system()} {platform.release()} | ({os.name})`",
                    inline=True)
    embed.add_field(name="Python version:",
                    value=f"`{pycpuinf['python_version']}`",
                    inline=False)
    embed.add_field(name="CPU:",
                    value=f"`{pycpuinf['brand_raw']}`",
                    inline=False)
    embed.add_field(name="GPU:",
                    value=f"`{gpu[:45]}`",
                    inline=False)
    embed.add_field(name="CPU Utilisation:",
                    value=f"`{cpu_usage}%`",
                    inline=True)
    embed.add_field(name="RAM Utilisation:",
                    value=f"`{ram_usage}%`",
                    inline=True)

    await ctx.edit_original_response(embed=embed, view=Buttons())

@bot.tree.command(name='avatar', description='it shows the users fucking avatar dumbass')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def mister_avatar(ctx: discord.Interaction, user: discord.User):
    embed = discord.Embed(title="avatar",
                      description="kys",
                      colour=0xae469c)

    embed.add_field(name="usr:",
                    value=f"{user.name}, {user.mention}",
                    inline=False)

    embed.set_image(url=f"{user.avatar.url}")

    await ctx.response.send_message(embed=embed)


@bot.tree.command(name='rand_caps', description='makes random letters bigg')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def mister_rand_caps(ctx: discord.Interaction, string: str):
    outputty = ''
    for letter in string:
        h = random.randint(1,2)
        if h == 2:
            outputty += letter.upper()
        else:
            outputty += letter
    await ctx.response.send_message(outputty, ephemeral=True)

@bot.tree.command(name='playing-sp', description='Show\'s currently playing media on spotify')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def mister_playing(ctx: discord.Interaction):
    if ctx.user.id != 1118973285766533250:
        await ctx.response.send_message(content='fock off matey 3:')
    else:
        view = discord.ui.View()
        
        current_track = sp.current_user_playing_track()

        if current_track is not None:
            track_name = current_track['item']['name']
            artist_name = current_track['item']['artists'][0]['name']
            album_name = current_track['item']['album']['name']
            album_images = current_track['item']['album']['images']
            album_image = album_images[0]["url"]
            song_url = current_track['item']['external_urls']['spotify']
            progress = milliseconds_to_minutes_seconds(current_track['progress_ms'])
            duration = milliseconds_to_minutes_seconds(current_track['item']['duration_ms'])
            explict = current_track['item']['explicit']
            view.add_item(discord.ui.Button(label="Spotify URL", style=1, url=song_url))
            embed = discord.Embed(title="Currently Playing",
                    colour=0x00b0f4)

            embed.add_field(name="Track name:",
                            value=f"{track_name}",
                            inline=True)
            embed.add_field(name="Artist:",
                            value=f"{artist_name}",
                            inline=False)
            embed.add_field(name="Album:",
                            value=f"{album_name}",
                            inline=False)
            embed.add_field(name="Progress:",
                            value=f"{progress}/{duration}",
                            inline=True)
            embed.add_field(name="Is explict:",
                            value=f'{explict}',
                            inline=True)
            
            embed.set_thumbnail(url=f"{album_image}")

            # embed.set_footer(text=f"Ran by {ctx.author.name}")
            await ctx.response.send_message(embed=embed, view=view)
        else:
            await ctx.response.send_message(content='Nothing is playing D:')


@bot.tree.command(name='samd-cta', description='Show\'s a samd car :3')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def mister_cutey_sand_car(ctx: discord.Interaction):
    await ctx.response.send_message(content='command removed for now :(')

@bot.tree.command(name='ping', description='ping a url/ip')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def mister_ping_thing(ctx: discord.Interaction, web: str):
    await ctx.response.send_message(content='loading :3')
    try:
        if "http://" in web or "https://" in web:
            pass
        else:
            web = "http://" + web
        try:
            request = requests.get(web, timeout=3)
        except requests.ConnectionError:
            embed = discord.Embed(title=f"Checking {web}",
                      url=f"{web}",
                      description="Connection error occured!")

            embed.set_author(name="Is up?")

            await ctx.edit_original_response(embed=embed)
        embed = discord.Embed(title=f"Checking {web}",
                      url=f"{web}",
                      description=f"Response CODE: {request.status_code}") 

        embed.set_author(name="Is up?")

        await ctx.edit_original_response(embed=embed)
    except Exception as e:
       await ctx.edit_original_response(content=f'A uncaptured and unexpected fucking error happened you fucking retarded cunt, {e}')

@bot.tree.command(name='yt-dl', description='Downloads specified video')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def mister_yt_download(ctx: discord.Interaction, *,url: str):
    if ctx.user.id == 0:
        pass
    else:
        embed = discord.Embed(description="Downloading...", colour=0xcba6f7)

        await ctx.response.send_message(embed=embed)
        try:

            yt_opts = {
                'verbose': False,
                'format': 'best',
                'download_archive': None,
                'restrictfilenames': True,
                'merge_output_format': 'mp4',
            }

            ydl = yt_dlp.YoutubeDL(yt_opts)

            with yt_dlp.YoutubeDL(yt_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                filesize = info_dict.get('filesize')
                if filesize is None:
                    formats = info_dict.get('formats', [])
                    for f in formats:
                        if f.get('format_id') == 'best':
                            filesize = f.get('filesize')
                            break
                
                filesize = filesize
            if filesize:
                if filesize > 524288000:
                    embed = discord.Embed(title="Error",
                      description="File too big!",
                      colour=0xcba6f7)
                    await ctx.edit_original_response(embed=embed)
                elif filesize < 524288000:
                    ydl.download([url])

                    for file in os.listdir('./'):
                        if file.endswith('.mp4'):
                            filename = file
                        else:
                            pass
                    
                    if os.path.getsize(f'./{filename}') > 25165824:
                        embed = discord.Embed(description="File bigger than 24MB!\nUploading to file server", colour=0xcba6f7)
                        await ctx.edit_original_response(embed=embed)
                        headers=({'Expires-At': '5m', "Authorization": sharex_server_token, "Override-Domain": "share.tomthepotato.xyz"})
                        files={'file': open(f'./{filename}', 'rb')}
                        r = requests.post(sharex_server_api, files=files, headers=headers)
                        print(r.json())
                        embed = discord.Embed(description="Uploaded!", colour=0xcba6f7)

                        embed.add_field(name="URL",
                                        value=f"{r.json()['files'][0]}",
                                        inline=False)
                        embed.add_field(name="Expires at",
                                        value=f"{r.json()['expiresAt']}",
                                        inline=False)

                        await ctx.followup.send(embed=embed)
                        await asyncio.sleep(1)
                        os.remove(f'./{filename}')
                        meow = await ctx.original_response()
                        await meow.delete()
                    else:
                        embed = discord.Embed(description="Downloaded!", colour=0xcba6f7)
                        await ctx.edit_original_response(embed=embed)
                        await ctx.followup.send(file=discord.File(f'./{filename}', filename=filename))
                        await asyncio.sleep(1)
                        os.remove(f'./{filename}')
                        meow = await ctx.original_response()
                        await meow.delete()
            else:
                embed = discord.Embed(title="Error", description="Unable to determine file size!\nUnable to continue", colour=0xcba6f7)
                await ctx.edit_original_response(embed=embed)
                
        except yt_dlp.DownloadError as e:
            embed = discord.Embed(title="Error",
                      description="Failed to download",
                      colour=0xcba6f7)

            embed.add_field(name="Log",
                            value=f"||```ascii\n{e}```||",
                            inline=False)
            await ctx.edit_original_response(embed=embed)
          
bot.run(bot_token)

