#  DEPRECATED; DO NOT USE.

import requests
import re
import json
import random
import os
import discord
from discord.ext import commands
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='+', intents=intents)
# bot = discord.Client(intents=intents, command_prefix='+')
    
def GwenSubRefresh():
    with open('GwenUsers.txt','r+') as f:
        global GwenSub
        GwenSub = []
        for line in f:
            GwenSub.append(line.strip().split('\n'))
            
def blacklistRefresh():
    with open('blacklist.txt','r+') as f:
        global blacklist
        blacklist = []
        for line in f:
            blacklist.append(line.strip().split('\n'))
            
GwenSubRefresh()
blacklistRefresh()
    
@client.event
async def on_ready():
    print('Bot enabled')

@client.listen('on_message')
async def on_message(msg):
    global GwenSub
    global blacklist
    GwenSubRefresh()
    if '+' not in msg.content:
        if any(str(msg.author.id) in sublist for sublist in GwenSub) and not any(str(msg.author.id) in sublist for sublist in blacklist):
            if msg.author == client.user:
                return
            if 'gwen' in msg.content.lower():
                ranNum = random.randint(0,99)
                if ranNum == 4:
                    await msg.channel.send('Gwen is... not immune?')
                    print(ranNum)
                else:
                    await msg.channel.send('Gwen is immune.')
                    print(ranNum)
            if 'gw3n' in msg.content.lower():
                await msg.channel.send('Gwen is immune. You cannot escape.')
    if msg.author.id == 252498411511742464:
        if 'sendshit' in msg.content:
            res = msg.content
            res = res.replace('sendshit','')
            channel = client.get_channel(410517986256879618)
            if "$" in msg.content:
                split = res.split("$",1)
                channel = client.get_channel(int(split[1]))
                res = split[0]
                res = res.replace("$",'')
            await channel.send(res)
    
response = requests.get("https://ddragon.leagueoflegends.com/cdn/12.11.1/data/en_US/champion.json")
champJson = str(json.loads(response.text))
eloList = ['All', 'Challenger', 'Master', 'Grandmaster', 'Diamond', 'Gold', 'Silver','Iron', 'Bronze', 'Diamond2Plus', 'MasterPlus', 'DiamondPlus', 'PlatinumPlus', 'Platinum']


@client.command(aliases=['winrate'])
async def wr(ctx, champ, elo=""):
  # finall champion names
  allChamp = re.findall(r"(?<='id':\s')[^']*", champJson)
  champ = champ[0].upper() + champ[1:]
  if elo != "":
    elo = elo[0].upper() + elo[1:]
  if elo in eloList:
    if champ in allChamp:
      champ = champ.lower()
      url = "https://app.mobalytics.gg/lol/champions/{}/build?rank={}".format(
        champ, elo)
      log = requests.get(url).content
      soup = BeautifulSoup(log, "html.parser")
      wR = soup.find_all(
        'span', {'style': 'color:var(--general-white-100)'})[0]
      wR = wR.text
      wR = float(wR.rstrip(wR[-1]))
      name = champ.capitalize()
      res = "{} has a {}% winrate in {} elo(s) based on their highest winrate build.".format(
        name, wR, elo)
      await ctx.send(res)
    elif champ == 'R' or champ == 'Random':
      random.seed
      num = random.randint(0, len(allChamp)-1)
      allChamp = allChamp[num]  # select random champion name
      champ = champ.lower()
      url = "https://app.mobalytics.gg/lol/champions/{}/build?={}".format(
        allChamp, elo)
      log = requests.get(url).content
      soup = BeautifulSoup(log, "html.parser")
      wR = soup.find_all(
        'span', {'style': 'color:var(--general-white-100)'})[0]
      wR = wR.text
      wR = float(wR.rstrip(wR[-1]))
      name = allChamp.capitalize()
      res = "{} has a {}% winrate in {} elo(s) based on their highest winrate build.".format(
        name, wR, elo)
      await ctx.send(res)
    else:
        await ctx.send("Invalid champion, check '+list' for a list of all acceptable IDs.")
  elif elo == "":
    if champ in allChamp:
      champ = champ.lower()
      url = 'https://app.mobalytics.gg/lol/champions/{}/build'.format(
        champ)
      log = requests.get(url).content
      soup = BeautifulSoup(log, "html.parser")
      for s in soup.select('span'):
        s.extract()
      wR = soup.find_all('td', class_='m-n4kcg9')[1]
      wR = wR.text
      wR = float(wR.rstrip(wR[-1]))
      name = champ.capitalize()
      res = "{} has a {}% overall winrate.".format(name, wR)
      await ctx.send(res)
    elif champ == 'R' or champ == 'Random':
      random.seed
      num = random.randint(0, len(allChamp)-1)
      allChamp = allChamp[num].lower()  # select random champion name
      url = 'https://app.mobalytics.gg/lol/champions/{}/build'.format(
        allChamp)
      log = requests.get(url).content
      soup = BeautifulSoup(log, "html.parser")
      for s in soup.select('span'):
        s.extract()
      wR = soup.find_all('td', class_='m-n4kcg9')[1]
      wR = wR.text
      wR = float(wR.rstrip(wR[-1]))
      name = allChamp.capitalize()
      res = "{} has a {}% overall winrate.".format(name, wR)
      await ctx.send(res)
    else:
      await ctx.send("Invalid champion, check '+list' for a list of all acceptable IDs.")
  else:
    await ctx.send("Invalid elo, check '+elolist' for a list of all acceptable elos. For elos with Plus at the end, capitalise the Plus.")

@client.command(pass_context=True)
async def list(ctx):
  # find all champion names
  allChamp = re.findall(r"(?<='id':\s')[^']*", champJson)
  user = ctx.message.author
  await user.send(allChamp)


@client.command(pass_context=True)
async def elolist(ctx):
  user = ctx.message.author
  await user.send(eloList)


@client.command(aliases=['Evasion'])
async def evasion(ctx):
  evas = "Active: Jax enters Evasion, a defensive stance, for up to 2 seconds, causing all basic attacks against him to miss. Jax also takes 25% reduced damage from all champion area of effect abilities. After 1 second, Jax can reactivate to end it immediately."
  await ctx.send(evas)


@client.command(aliases=['gwen', 'immune'])
async def g(ctx):
  gwen = "Gwen is immune."
  await ctx.send(gwen)


@client.command(aliases=['Aatrox'])
async def aatrox(ctx):
  aatrox = "Aatrox got ignited."
  await ctx.send(aatrox)

@client.command(aliases=['lh','Lh','LH'])
async def listenhere(ctx):
    listen = "Listen here you little shit"
    await ctx.send(listen)

@client.command(aliases=['Emo'])
async def emo(ctx):
  emo = "Aatrox's biggest fan (owns an Aatrox tshirt)"
  await ctx.send(emo)

@client.command(aliases=['gwenadd','Gwenadd','gwensub'])
async def GwenAdd(ctx):
    user = ctx.author.id
    if not any(str(user) in sublist for sublist in GwenSub):
        with open('GwenUsers.txt','a') as f:
            f.write(f'\n{user}')
        GwenSubRefresh()
        await ctx.send('User added to GwenBot Subscription.')
    else:
        await ctx.send('You are already subscribed to GwenBot.')


@client.command(aliases=['gwenremove','subremove'])
async def remove(ctx):
    user = str(ctx.author.id)
    if not any(str(user) in sublist for sublist in GwenSub):
        await ctx.send('You are not subscribed to GwenBot.')
    else:
        with open('GwenUsers.txt','r') as f:
            lines = f.readlines()
        with open('GwenUsers.txt','w') as f:
            for line in lines:
                if line.strip('\n') != user:
                    f.write(line)
        GwenSubRefresh()
        await ctx.send('User removed from GwenBot Subscription.')
        
@client.command(aliases=['bl','blacklist'])
@commands.has_permissions(kick_members=True)
async def blpass(ctx, id):
    with open('blacklist.txt','a') as f:
        f.write(f'\n{str(id)}')
    blacklistRefresh()
    await ctx.send('User added to blacklist.')
    
# @client.command()
# async def fuckyou(ctx, id):
#     if ctx.author.id == 252498411511742464:
#     	with open('blacklist.txt','a') as f:
#         f.write(f'\n{str(id)}')
#     	blacklistRefresh()
#     	await ctx.send('User added to blacklist.')
        
@client.command()
async def unfuckyou(ctx, id):
    if ctx.author.id == 252498411511742464:
        with open('blacklist.txt', 'r') as f:
            lines = f.readlines()
        with open('blacklist.txt', 'w') as f:
            for line in lines:
                if line.strip('\n') != str(id):
                    f.write(line)
        blacklistRefresh()
        await ctx.send('User removed from blacklist.')

@client.command(aliases=['blremove','blr','blacklistremove'])
@commands.has_permissions(kick_members=True)
async def blpassremove(ctx, id):
    with open('blacklist.txt','r') as f:
        lines = f.readlines()
    with open('blacklist.txt','w') as f:
        for line in lines:
            if line.strip('\n') != str(id):
                f.write(line)
    blacklistRefresh()
    await ctx.send('User removed from blacklist.')
    
@client.command(aliases=['george','George','Sylas'])
async def sylas(ctx):
    sylas = 'Sylas pressed W.'
    await ctx.send(sylas)

@client.command(aliases=['Menu'])
async def menu(ctx):
  _help = """
  +winrate (champion, elo) - Gives the winrate of the named champion. If no elo is given, the bot will return the overall winrate across all elos. If an elo was given, the bot gives the best performing build for that elo.

  +wr (champion, elo) - Alternative to winrate.

  +wr (r/random, elo) - Gives the winrate of a random champion. Same arguments as for the normal winrate command.
  
  +gwenadd (+gwensub) - Adds you to the list of Gwen auto replies. If you type gwen anywhere in your message, the bot will reply with 'Gwen is immune.'.
  
  +remove - Removes you from the list of Gwen auto replies.

  +list - Gives a list of acceptable champion names.

  +elolist - Gives a list of acceptable elos.

  +evasion - Jax enters evasion
  
  +g (gwen, immune) - Gwen is immune.
  
  +listenhere (lh) - Listen here you little shit
  
  +aatrox - Aatrox got ignited.
  
  +emo - beta male
 
  +sylas - Sylas pressed W."""
  user = ctx.message.author
  await user.send(_help)

@client.command()
async def shutdown(ctx):
    if ctx.message.author.id == 252498411511742464: #replace OWNERID with your user id
        print("shutdown")
        try:
            await ctx.client.close()
        except:
            print("EnvironmentError")
            client.clear()
    else:
        await ctx.send("You do not own this bot!")

client.run('TOKEN')