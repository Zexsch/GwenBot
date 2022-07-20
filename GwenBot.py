import requests
import re
import json
import random
import os
from discord.ext import commands
from bs4 import BeautifulSoup

client = commands.Bot(command_prefix='+')

def GwenSubRefresh(): # Refreshes the list of all people that have subscribed to gwenbot
    with open('GwenUsers.txt','r+') as f: # You NEED to have a file called GwenUsers.txt in the same directory
        global GwenSub
        GwenSub = []
        for line in f:
            GwenSub.append(line.strip().split('\n'))
            
def blacklistRefresh(): # refreshes the blacklist
    with open('blacklist.txt','r+') as f: # You NEED to have a file called blacklist.txt in the same directory
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
                await msg.channel.send('Gwen is immune.') # Can easily be done in a more efficient way by switching if statements but I cba it runs fine
    if msg.author.id == 252498411511742464:  # My ID, this allows me to communicate through the bot
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


@client.command(aliases=['winrate']) # The spacing here is really fucked, that's cause the server I'm hosting it on is really fucking weird with indentation
async def wr(ctx, champ, elo=""): # So you might need to fix this
  # findall champion names
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
      wR = soup.find_all('td', class_='m-m7fsih')[1]
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
      wR = soup.find_all('td', class_='m-m7fsih')[1]
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

@client.command(aliases=['gwenadd','Gwenadd','gwensub']) # Adds the user to the list of all subscribed users
async def GwenAdd(ctx):
    user = ctx.author.id
    if not any(str(user) in sublist for sublist in GwenSub):
        with open('GwenUsers.txt','a') as f:
            f.write(f'\n{user}')
        GwenSubRefresh()
        await ctx.send('User added to GwenBot Subscription.')
    else:
        await ctx.send('You are already subscribed to GwenBot.')


@client.command(aliases=['gwenremove','subremove']) # Removes the user from the sublist
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
@commands.has_permissions(kick_members=True) # Makes it so that anyone with kick perms can add users to the blacklist
async def blpass(ctx, id): # This bot is supposed to be used on a single server, if you'd want to copy it, make it create a new file for each server
    with open('blacklist.txt','a') as f:
        f.write(f'\n{str(id)}')
    blacklistRefresh()
    await ctx.send('User added to blacklist.')
    
@client.command()
async def fuckyou(ctx, id):
    if ctx.author.id == 252498411511742464: # my discord ID lmao, just allows me to add a user to the blacklist whenever I want
    	with open('blacklist.txt','a') as f:
        	f.write(f'\n{str(id)}')
    	blacklistRefresh()
    	await ctx.send('User added to blacklist.')

@client.command(aliases=['blremove','blr','blacklistremove']) # Removes a user from the blacklist
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

@client.command(aliases=['Menu']) # Need to update this, it's shit
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

@client.command() # Manual shutdown as a command
async def shutdown(ctx):
    if ctx.message.author.id == 252498411511742464: 
        print("shutdown")
        try:
            await ctx.client.close()
        except:
            print("EnvironmentError")
            client.clear()
    else:
        await ctx.send("You do not own this bot!")

client.run(TOKEN)
