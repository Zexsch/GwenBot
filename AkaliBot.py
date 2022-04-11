import requests, re, json, random, os
from discord.ext import commands
from bs4 import BeautifulSoup
from keep_alive import keep_alive

client = commands.Bot(command_prefix='+')

@client.event
async def on_ready():
  print('Bot enabled')

response = requests.get("https://ddragon.leagueoflegends.com/cdn/12.1.1/data/en_US/champion.json")
champJson = str(json.loads(response.text))
eloList = ['All','Challenger','Master','Grandmaster','Diamond','Gold','Silver','Iron','Bronze','Diamond2Plus','MasterPlus','DiamondPlus','PlatinumPlus', 'Platinum']

@client.command(aliases=['winrate'])
async def wr(ctx, champ, elo=""):
  allChamp = re.findall(r"(?<='id':\s')[^']*", champJson)#finall champion names
  champ = champ[0].upper() + champ[1:]
  if elo != "":
    elo = elo[0].upper() + elo[1:]
  if elo in eloList:
    if champ in allChamp:
      champ = champ.lower()
      url = "https://app.mobalytics.gg/lol/champions/{}/build?rank={}".format(champ, elo)
      log = requests.get(url).content
      soup = BeautifulSoup(log, "html.parser")      
      wR = soup.find_all('span', {'style':'color:var(--general-white-100)'})[0]
      wR = wR.text
      wR = float(wR.rstrip(wR[-1]))
      name = champ.capitalize()
      res = "{} has a {}% winrate in {} elo(s) based on their highest winrate build.".format(name,wR,elo)
      await ctx.send(res)
    elif champ == 'R' or champ == 'Random':
      random.seed
      num = random.randint(0, len(allChamp)-1)
      allChamp = allChamp[num] # select random champion name
      champ = champ.lower()
      url = "https://app.mobalytics.gg/lol/champions/{}/build?={}".format(allChamp, elo)
      log = requests.get(url).content
      soup = BeautifulSoup(log, "html.parser")      
      wR = soup.find_all('span', {'style':'color:var(--general-white-100)'})[0]
      wR = wR.text
      wR = float(wR.rstrip(wR[-1]))
      name = allChamp.capitalize()
      res = "{} has a {}% winrate in {} elo(s) based on their highest winrate build.".format(name,wR,elo)
      await ctx.send(res)
    else:
      await ctx.send("Invalid champion, check '+list' for a list of all acceptable IDs.")
  elif elo == "":
    if champ in allChamp:
      champ = champ.lower()
      url = 'https://app.mobalytics.gg/lol/champions/{}/build'.format(champ)
      log = requests.get(url).content
      soup = BeautifulSoup(log, "html.parser")
      for s in soup.select('span'):
        s.extract()
      wR = soup.find_all('td', class_='m-m7fsih')[1]
      wR = wR.text
      wR = float(wR.rstrip(wR[-1]))
      name = champ.capitalize()
      res = "{} has a {}% overall winrate.".format(name,wR)
      await ctx.send(res)
    elif champ == 'R' or champ == 'Random':
      random.seed
      num = random.randint(0, len(allChamp)-1)
      allChamp = allChamp[num].lower() # select random champion name
      url = 'https://app.mobalytics.gg/lol/champions/{}/build'.format(allChamp)
      log = requests.get(url).content
      soup = BeautifulSoup(log, "html.parser")
      for s in soup.select('span'):
        s.extract()
      wR = soup.find_all('td', class_='m-m7fsih')[1]
      wR = wR.text
      wR = float(wR.rstrip(wR[-1]))
      name = allChamp.capitalize()
      res = "{} has a {}% overall winrate.".format(name,wR)
      await ctx.send(res)
    else:
      await ctx.send("Invalid champion, check '+list' for a list of all acceptable IDs.")
  else:
    await ctx.send("Invalid elo, check '+elolist' for a list of all acceptable elos. For elos with Plus at the end, capitalise the Plus.")
    

@client.command(pass_context=True)
async def list(ctx):
  allChamp = re.findall(r"(?<='id':\s')[^']*", champJson) # find all champion names
  user = ctx.message.author
  await user.send(allChamp)

@client.command(pass_context=True)
async def elolist(ctx):
  user = ctx.message.author
  await user.send(eloList)

@client.command()
async def evasion(ctx):
  evas = "Active: Jax enters Evasion, a defensive stance, for up to 2 seconds, causing all basic attacks against him to miss. Jax also takes 25% reduced damage from all champion area of effect abilities. After 1 second, Jax can reactivate to end it immediately."
  await ctx.send(evas)

@client.command(aliases=['gwen','immune'])
async def g(ctx):
  gwen = "Gwen is immune."
  await ctx.send(gwen)

@client.command()
async def aatrox(ctx):
  aatrox = "Aatrox got ignited."
  await ctx.send(aatrox)

@client.command()
async def emo(ctx):
  emo = "Aatrox's biggest fan (owns an aatrox tshirt)"
  await ctx.send(emo)

@client.command()
async def menu(ctx):
  _help = """
  +winrate (champion, elo) - gives the winrate of the named champion. If no elo is given, the bot will return the overall winrate across all elos. If an elo was given, the bot gives the best performing build for that elo.

  +wr (champion, elo) - alternative to winrate.

  +wr (r/random, elo) - gives the winrate of a random champion. Same arguments as for the normal winrate command.

  +list - gives a list of acceptable champion names.

  +elolist - gives a list of acceptable elos.

  +evasion - jax enters evasion
  
  +g (gwen, immune) - Gwen is immune.
  
  +aatrox - Aatrox got ignited.
  
  +emo - beta male"""
  user = ctx.message.author
  await user.send(_help)

keep_alive()

client.run(os.environ['TOKEN'])
