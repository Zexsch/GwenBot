from ast import alias
import discord
import logging
import gc
import datetime

from discord.ext import commands
from discord.ext import tasks
from bs4 import BeautifulSoup
from requests import get as getreq
from requests.exceptions import RequestException
from json import loads as loadsjson
from random import randint
from openai import AsyncOpenAI
# from re import findall

# from .Database.database import Database
# from .Config.config import (LOL_VERSION, OWNER_ID, DEFAULT_CHANNEL, PREFIX)
from Database.database import Database
from .helpmsg import (helpmsg, wrhelpmsg)
from Config.config import (LOL_VERSION, OWNER_ID, DEFAULT_CHANNEL, PREFIX, MESSAGE_CHANNEL, DEEPSEEK_TOKEN)

class Bot(commands.Bot, Database, commands.Cog):
    def __init__(self):
        """
        Create an instance of the bot then do the run('TOKEN') command, replace TOKEN with your discord bot token. 
        League of Legends Gwen-themed discord bot. 
        Fetches the winrate of any given LOL champion via web scraping on u.gg 
        Also replies to any message containing 'Gwen' in any way [optional, opt-in] 
        Has Deepseek reasoning integration
        Has some random fun commands. 
        """
        
        self.create_db()
        
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True
        
        commands.Bot.__init__(self, command_prefix=PREFIX, intents=intents, help_command=None, owner_id=OWNER_ID)
        
        self.response = getreq(f"https://ddragon.leagueoflegends.com/cdn/{LOL_VERSION}/data/en_US/champion.json")
        self.champion_json: dict[str, str] = loadsjson(self.response.text)
        self.elo_list: list[str] = ['overall', 'challenger', 'master', 'grandmaster', 'diamond', 'platinum', 'emerald',  
                                    'gold', 'silver', 'bronze', 'iron', 'diamond_2_plus', 'master_plus', 
                                    'diamond_plus', 'platinum_plus']
        self.role_list: list[str] = ['top', 'jungle', 'mid', 'adc', 'support']
        
        # Alternative names for the elos to use in +wr.
        self.alternative_elos: dict[str, str] = {
            'platinum': ['platplus', 'plat+', 'platinumplus'],
            'diamond2': ['d2+', 'd2', 'd2plus', 'diamond2', 'diamond2plus', 'diamond2+', 'diamond_2plus', 'diamond_2+'],
            'diamond': ['d+', 'dplus', 'diamondplus'],
            'master': ['m+', 'master+', 'masterplus', 'masters', 'masters+', 'mastersplus']
        }
        
        #  Regex version, not recommended
        #  self._all_champions: List[str] = findall(r"(?<='id':\s')[^']*", self.champion_json)
        #  self.all_champions: List[str] = [i.capitalize() for i in self._all_champions]    
        self.all_champions: list[str] = [i.capitalize() for i in self.champion_json['data']]
        
        
        # logger config
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(levelname)s : %(asctime)s : %(message)s', datefmt='%y/%m/%d %H:%M:%S')
        
        file_handler = logging.FileHandler('bot_log.log')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)

        
        
        self.add_commands()

        self.deepseek_client = AsyncOpenAI(api_key=DEEPSEEK_TOKEN, base_url="https://api.deepseek.com")

        self.ugg_div_values = ['shinggo', 'good', 'okay', 'volxd', 'meh']

        
    
        
    async def check_amount(self):
        count = 0

        async for _ in self.get_channel(MESSAGE_CHANNEL).history(limit=None):
            count += 1
        
        count = count - 1
        self.set_amount(count)

    
    async def on_ready(self) -> None:
        await self.check_amount()
        self.mudae_ping.start()
        self.logger.info('Bot enabled.')

    utc = datetime.timezone.utc
    
    times = [
        datetime.time(hour=2, tzinfo=utc),
        datetime.time(hour=4, tzinfo=utc),
        datetime.time(hour=6, tzinfo=utc),
        datetime.time(hour=8, tzinfo=utc),
        datetime.time(hour=10, tzinfo=utc),
        datetime.time(hour=12, tzinfo=utc),
        datetime.time(hour=14, tzinfo=utc),
        datetime.time(hour=16, tzinfo=utc),
        datetime.time(hour=18, tzinfo=utc),
        datetime.time(hour=20, tzinfo=utc),
        datetime.time(hour=22, tzinfo=utc),
        datetime.time(hour=00, tzinfo=utc)
    ]


    @tasks.loop(time=times)
    async def mudae_ping(self):
        await self.wait_until_ready()
        channel = self.get_channel(1320437220116791406)
        await channel.send("<@&1320528669684535358> Your mudae claim is up, disgusting addict weeb")
        

    
    def alternative_elo_names(self, elo: str) -> str|str:
        if elo in self.alternative_elos.get('platinum'):
            return ('platinum_plus', 'plat+', '')
        elif elo in self.alternative_elos.get('diamond2'):
            return ('diamond_2_plus', 'd2+', '')
        elif elo in self.alternative_elos.get('diamond'): 
            return ('diamond_plus', 'd+', '')
        elif elo in self.alternative_elos.get('master'):
            return ('master_plus', 'master+', '')
        else:
            return (elo, elo, None)
        
    
    def fetch_wr_with_elo(self, champ: str, elo: str, opp: str = None, role: str = None) -> float | None:
        r"""Return the winrate of a champion in a specified elo. Return :class:`None` if website is not reachable."""
        
        if not opp:
            if not role:
                if elo == 'Platinum_plus':
                    url = f'https://u.gg/lol/champions/{champ}/build'
                else:
                    url = f'https://u.gg/lol/champions/{champ}/build?rank={elo}'
            else:
                if elo == 'Platinum_plus':
                    url = f'https://u.gg/lol/champions/{champ}/build/{role}'
                else:
                    url = f'https://u.gg/lol/champions/{champ}/build/{role}?rank={elo}'
        else:
            if not role:
                if elo == 'Platinum_plus':
                    url = f'https://u.gg/lol/champions/{champ}/build?opp={opp}'
                else:
                    url = f'https://u.gg/lol/champions/{champ}/build?rank={elo}&opp={opp}'
            else:
                if elo == 'Platinum_plus':
                    url = f'https://u.gg/lol/champions/{champ}/build/{role}?opp={opp}'
                else:
                    url = f'https://u.gg/lol/champions/{champ}/build/{role}?rank={elo}&opp={opp}'
        
        try:
            web = getreq(url, headers={'User-Agent': 'Mozilla/5.0'}).content
        except RequestException:
            self.logger.error('Bot encountered an error when scraping u.gg.')
            return
        
        soup = BeautifulSoup(web, "html.parser")

        win_rate: str = ""
        repeat_count: int = 0

        while not win_rate:
            if repeat_count >= 5:
                self.logger.error(f'Index out of range error in +wr elo win_rate. champ={champ}, elo={elo}, url={url}')
                break

            try:
                win_rate: str = soup.find('div', {'class':f'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold {self.ugg_div_values[repeat_count]}-tier'}).text

            except:
                repeat_count += 1
            
            else: break
        
        if not win_rate:
            self.logger.error("Winrate wasn't found.")
            return
        
        try:
            win_rate = float(win_rate.rstrip(win_rate[-1]))
        except: pass
        
        if not isinstance(win_rate, float):
            win_rate: str = ""
            repeat_count: int = 4

            while not win_rate:
                if repeat_count <= -1:
                    self.logger.error(f'Index out of range error in +wr elo win_rate. champ={champ}, elo={elo}, url={url}')
                    break

                try:
                    win_rate: str = soup.find('div', {'class':f'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold {self.ugg_div_values[repeat_count]}-tier'}).text
                    
                    if not isinstance(win_rate, float):
                        win_rate: str = soup.find_all('div', {'class':f'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold {self.ugg_div_values[repeat_count]}-tier'})[1].text

                except:
                    repeat_count -= 1

                else: break
        
        if not isinstance(win_rate, float):
            try:
                win_rate = float(win_rate.rstrip(win_rate[-1]))
            except ValueError:
                self.logger.error(f'Winrate fetched was not a float. Given winrate: {win_rate}')
                return
        
        try:
            if not opp:
                match_count: str = soup.find_all('div', {'class':'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold'})[3].text
            else:
                match_count: str = soup.find('div', {'class':'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold'}).text
        except IndexError:
            self.logger.error(f'Index out of range error in +wr elo match_count. champ={champ}, elo={elo}, url={url}')
            return
        
        return (win_rate, match_count)

    def fetch_wr_without_elo(self, champ: str, opp: str = None, role: str = None) -> float | None:
        r"""Return the winrate of a champion without a specified elo. Return :class:`None` if website is not reachable."""
        
        if not opp:
            if not role:
                url = f'https://u.gg/lol/champions/{champ}/build?rank=overall'
            else:
                url = f'https://u.gg/lol/champions/{champ}/build/{role}?rank=overall'
        else:
            if not role:
                url = f'https://u.gg/lol/champions/{champ}/build?rank=overall&opp={opp}'
            else:
                url = f'https://u.gg/lol/champions/{champ}/build/{role}?rank=overall&opp={opp}'
        
        try:
            web = getreq(url, headers={'User-Agent': 'Mozilla/5.0'}).content
        except RequestException:
            self.logger.error('Bot encountered an error when scraping u.gg.')
            return
        
        soup = BeautifulSoup(web, "html.parser")

        win_rate: str = ""
        repeat_count: int = 0

        while not win_rate:
            if repeat_count >= 5:
                self.logger.error(f'Index out of range error in +wr elo win_rate. champ={champ}, url={url}')
                break

            try:
                win_rate: str = soup.find('div', {'class':f'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold {self.ugg_div_values[repeat_count]}-tier'}).text

            except:
                repeat_count += 1
            
            else: break
        
        if not win_rate:
            self.logger.error("Winrate wasn't found.")
            return
        
        try:
            win_rate = float(win_rate.rstrip(win_rate[-1]))
        except: pass

        if not isinstance(win_rate, float):
            win_rate: str = ""
            repeat_count: int = 4

            while not win_rate:
                if repeat_count <= -1:
                    self.logger.error(f'Index out of range error in +wr elo win_rate. champ={champ}, url={url}')
                    break
    
                try:
                    win_rate: str = soup.find('div', {'class':f'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold {self.ugg_div_values[repeat_count]}-tier'}).text
                    
                    if not isinstance(win_rate, float):
                        win_rate: str = soup.find_all('div', {'class':f'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold {self.ugg_div_values[repeat_count]}-tier'})[1].text
    
                except:
                    repeat_count -= 1
                
                else: break
        if not isinstance(win_rate, float):
            try:
                win_rate = float(win_rate.rstrip(win_rate[-1]))
            except ValueError:
                self.logger.error(f'Winrate fetched was not a float. Given winrate: {win_rate}')
                return

        try:
            if not opp:
                match_count: str = soup.find_all('div', {'class':'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold'})[3].text
            else:
                match_count: str = soup.find('div', {'class':'text-[20px] max-sm:text-[16px] max-xs:text-[14px] font-extrabold'}).text
        except IndexError:
            self.logger.error(f'Index out of range error in +wr elo match_count. champ={champ}, url={url}')
            return
        
        return (win_rate, match_count)

        
        
    def add_commands(self) -> None:
        """Add all discord events, commands and listeners in this."""

        @self.listen('on_message')
        async def on_message(msg: discord.Message) -> None:
            """There can only be one on-message listener so you need to add all listen-related events in this function."""


            """Question mark counter"""
            if msg.channel.id == MESSAGE_CHANNEL:

                if msg.content != '?':
                    channel = self.get_channel(410517986256879618)
                    if not '@' in msg.content:
                        await channel.send(f'<@341238409311944705> <@281791015411646464> Somebody did a little fucky wuckie >.<!! A small oopsie woopsie uwu! Someone dared ruin the ? chain nya~!!! <@{msg.author.id}> what have you done!! (⁄ ⁄•⁄ω⁄•⁄ ⁄) They dared send "{msg.content}" in our holy channel nya!')
                    else:
                        await channel.send(f'<@341238409311944705> <@281791015411646464> Somebody did a little fucky wuckie >.<!! A small oopsie woopsie uwu! Someone dared ruin the ? chain nya~!!! <@{msg.author.id}> what have you done!! (⁄ ⁄•⁄ω⁄•⁄ ⁄) They dared use an "@" in our holy channel nya!')
                    return

                if self.fetch_latest_user()[0] == msg.author.id:
                    channel = self.get_channel(410517986256879618)
                    await channel.send(f'<@341238409311944705> <@281791015411646464> Somebody did a little fucky wuckie >.<!! A small oopsie woopsie uwu! Someone dared ruin the ? chain nya~!!! <@{msg.author.id}> what have you done!! (⁄ ⁄•⁄ω⁄•⁄ ⁄) They dared send two ?s in a row nya!')
                    return
                
                self.set_latest_user(msg.author.id)

                current = self.fetch_amount()[0][0]
                current += 1
                self.set_amount(current)

            
            if PREFIX in msg.content:
                return
            
            if msg.guild is None:
                return
            
            """Make the bot send any message. Only usable by bot owner.
            sendshit (message)$(channel id)[optional]
            Trigger on-message, not a command."""
            if msg.author.id == OWNER_ID and 'sendshit' in msg.content.lower():
                res: str = msg.content
                res = res.replace('sendshit','')
                channel = self.get_channel(DEFAULT_CHANNEL)  # Default channel to send to. Change in Config.config.
                
                if "$" in msg.content:
                    split = res.split("$",1)
                    channel = self.get_channel(int(split[1]))
                    res = split[0]
                    res = res.replace("$",'')
                
                await channel.send(res)
                return
            

            """Make the bot reply to any message containing 'Gwen' in any way. Opt-in via +gwenadd."""
            if 'gwen' in msg.content.lower():
                if not self.fetch_gwen_sub(msg.author.id, msg.guild.id) or msg.author == self.user:
                    return

                if self.fetch_quote(msg.guild.id):
                    return
                
                ran_num: int = randint(0,99)
                
                if ran_num == 1:
                    await msg.channel.send('Gwen is... not immune?')
                    return
                else:
                    await msg.channel.send('Gwen is immune.')
                    return
            elif 'gw3n' in msg.content.lower():
                if not self.fetch_gwen_sub(msg.author.id, msg.guild.id) or msg.author == self.user:
                    return
                await msg.channel.send('Gwen is immune. You cannot escape.')
                return
        
        #
        #  WINRATE COMMANDS
        #
        
        @self.command(aliases=['winrate'])
        async def wr(ctx: commands.Context, champ: str, *args) -> None:
            """Make the bot send the winrate of a given champ in a specified elo. \n
            +wr (winrate) | (champion, r, random) (elo[optional]) (opposing champ[optional]) \n
            Choosing r or random as a parameter will randomly select a champion from the list of all champions. \n
            Elo is optional.
            Opponent is optional.
            Role is optional.
            """
            
            elo: str = ''
            opp: str = ''
            role: str = ''
            champ: str = champ.capitalize()
            
            if args:
                for arg in args:
                    if arg.lower() in self.elo_list or self.alternative_elo_names(arg.lower())[2] != None:
                        elo_tuple: str = self.alternative_elo_names(arg.lower())
                        elo = elo_tuple[0]
                    
                    if arg.capitalize() in self.all_champions:
                        opp = arg
                        
                    if arg.lower() in self.role_list:
                        role = arg
                        
            if champ not in self.all_champions and (champ != 'R' or champ != 'Random'):
                await ctx.send('Invalid champion. Check +list for a list of all accepted champions.')
                return
            
            #  If elo is given
            if elo != '' and champ in self.all_champions:
                champ = champ.lower()
                
                if opp:
                    if role:
                        info = self.fetch_wr_with_elo(champ=champ, elo=elo, opp=opp, role=role)
                    else:
                        info = self.fetch_wr_with_elo(champ=champ, elo=elo, opp=opp)
                else:
                    if role:
                        info = self.fetch_wr_with_elo(champ=champ, elo=elo, role=role)
                    else:
                        info = self.fetch_wr_with_elo(champ=champ, elo=elo)
                    
                win_rate: float | None = info[0]
                
                if not win_rate:
                    await ctx.send('An error occured when fetching the winrate. Is u.gg down?')
                    return
                
                champ = champ.capitalize()
                
                if not opp:
                    if not role:
                        await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} with {info[1]} matches played.')
                    else:
                        await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} in {role} with {info[1]} matches played.')
                else:
                    if not role:
                        await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} against {opp.capitalize()} with {info[1]} matches played.')
                    else:
                        await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} against {opp.capitalize()} in {role} with {info[1]} matches played.')
                return
            
            elif elo != '' and (champ == 'R' or champ == 'Random'):
                
                num: int = randint(0, len(self.all_champions)-1)
                champ: str = self.all_champions[num]
                
                champ = champ.lower()
                
                if opp:
                    if role:
                        info = self.fetch_wr_with_elo(champ=champ, elo=elo, opp=opp, role=role)
                    else:
                        info = self.fetch_wr_with_elo(champ=champ, elo=elo, opp=opp)
                else:
                    if role:
                        info = self.fetch_wr_with_elo(champ=champ, elo=elo, role=role)
                    else:
                        info = self.fetch_wr_with_elo(champ=champ, elo=elo)
                        
                win_rate: float | None = info[0]
                
                if not win_rate:
                    await ctx.send('An error occured when fetching the winrate. Is u.gg down?')
                    return

                champ = champ.capitalize()            
                
                if not opp:
                    if not role:
                        await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} with {info[1]} matches played.')
                    else:
                        await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} in {role} with {info[1]} matches played.')
                else:
                    if not role:
                        await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} against {opp.capitalize()} with {info[1]} matches played.')
                    else:
                        await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} against {opp.capitalize()} in {role} with {info[1]} matches played.')
                return
            
            #  If elo is not given
            if elo == '' and champ in self.all_champions:
                
                champ = champ.lower()
                
                if opp:
                    if role:
                        info = self.fetch_wr_without_elo(champ=champ, opp=opp, role=role)
                    else:
                        info = self.fetch_wr_without_elo(champ=champ, opp=opp)
                else:
                    if role:
                        info = self.fetch_wr_without_elo(champ=champ, role=role)
                    else:
                        info = self.fetch_wr_without_elo(champ=champ)
                        
                win_rate: float | None = info[0]
                
                if not win_rate:
                    await ctx.send('An error occured when fetching the winrate. Is u.gg down?')
                    return
                
                champ = champ.capitalize()
                
                if not opp:
                    if not role:
                        await ctx.send(f'{champ} has a {win_rate}% overall winrate with {info[1]} matches played.')
                    else:
                        await ctx.send(f'{champ} has a {win_rate}% overall winrate in {role} with {info[1]} matches played.')
                else:
                    if not role:
                        await ctx.send(f'{champ} has a {win_rate}% overall winrate against {opp.capitalize()} with {info[1]} matches played.')
                    else:
                        await ctx.send(f'{champ} has a {win_rate}% overall winrate against {opp.capitalize()} in {role} with {info[1]} matches played.')
                return
            
            elif elo == '' and (champ == 'R' or champ == 'Random'):
                num: int = randint(0, len(self.all_champions)-1)
                champ: str = self.all_champions[num]
                
                champ = champ.lower()
                
                if opp:
                    info = self.fetch_wr_without_elo(champ=champ, opp=opp)
                else:
                    info = self.fetch_wr_without_elo(champ=champ)
                    
                win_rate: float | None = info[0]
                
                if not win_rate:
                    await ctx.send('An error occured when fetching the winrate. Is u.gg down?')
                    return
                
                champ = champ.capitalize()
                
                if not opp:
                    if not role:
                        await ctx.send(f'{champ} has a {win_rate}% overall winrate with {info[1]} matches played.')
                    else:
                        await ctx.send(f'{champ} has a {win_rate}% overall winrate in {role} with {info[1]} matches played.')
                else:
                    if not role:
                        await ctx.send(f'{champ} has a {win_rate}% overall winrate against {opp.capitalize()} with {info[1]} matches played.')
                    else:
                        await ctx.send(f'{champ} has a {win_rate}% overall winrate against {opp.capitalize()} in {role} with {info[1]} matches played.')
                return


        #
        #  GWENBOT SUBSCRIPTION COMMANDS
        #
        
        @self.command(name='GwenAdd', pass_context=True, aliases=['add', 'gwenadd'])
        async def gwen_add(ctx: commands.Context):
            """Command to add user to the subscribed database"""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
            
            if self.fetch_blacklist(ctx.author.id, ctx.guild.id):
                await ctx.send('You are blacklisted from using this function.')
                return
            
            if self.fetch_quote(ctx.guild.id):
                await ctx.send('The server has blocked this function.')
                return
            
            if not self.fetch_gwen_sub(ctx.author.id, ctx.guild.id):
                self.add_to_gwen_sub(ctx.author.id, ctx.guild.id)
                await ctx.send('Successfully subscribed to GwenBot.')
                
                self.logger.info(f'User {ctx.author.id} Server {ctx.guild.id} added to GwenBot subscription.')
            else:
                await ctx.send('You are already subscribed to GwenBot.')
        
        @self.command(name='remove', pass_context=True, aliases=['gwenremove', 'Gwenremove', 'rem', 'removesub'])
        async def gwen_remove(ctx: commands.Context) -> None:
            """Command to remove user from the subscribed database"""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
            
            if self.fetch_gwen_sub(ctx.author.id, ctx.guild.id):
                self.remove_from_gwen_sub(ctx.author.id, ctx.guild.id)
                await ctx.send('Successfully removed from the GwenBot Subscription.')
                
                self.logger.info(f'User {ctx.author.id} Server {ctx.guild.id} removed from GwenBot subscription.')
            else:
                await ctx.send('You are not currently subscribed to GwenBot.', ephemeral=True)
        
        @self.command(name='checkgs', pass_context=True, aliases=['checksub'])
        async def checkgs(ctx: commands.Context, id=None) -> None:
            """Command to check if a user is subbed. +checkgs id[optional]"""
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
            
            if id == None:
                if self.fetch_gwen_sub(ctx.author.id, ctx.guild.id):
                    await ctx.send('You are subscribed.')
                else:
                    await ctx.send('You are not subscribed.')
            else:
                try:
                    id = int(id)
                except ValueError:
                    if len(ctx.message.mentions) == 0:
                        await ctx.send('Invalid id...', ephemeral=True)
                        return
                    else:
                        id = ctx.message.mentions[0].id
                
                if self.fetch_gwen_sub(id, ctx.guild.id):
                    await ctx.send('User is Subscribed.')
                else:
                    await ctx.send('User is not Subscribed.')
        
        @commands.has_permissions(kick_members=True)    
        @self.command(name='quote', pass_context=True)
        async def quote(ctx: commands.Context, id=None) -> None:
            """Command to add/undo Quote"""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
            
            if id == None:
                if self.fetch_quote(ctx.guild.id):
                    self.remove_from_quote(ctx.guild.id)
                    await ctx.send('Gwen will now respond to chat.')
                else:
                    self.add_to_quote(ctx.guild.id)
                    await ctx.send('Gwen will no longer respond to chat.')
                    
        
        @self.command(name='modremove', pass_context=True)
        @commands.has_permissions(kick_members=True)
        async def removesubmod(ctx: commands.Context, id) -> None:
            """Command to forcefully remove a user from the GwenBot subscription.
            Usable only by users with kick_members permissions."""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
            
            try: 
                id = int(id)
            except ValueError:
                if len(ctx.message.mentions) == 0:
                    await ctx.send('Invalid id...', ephemeral=True)
                    return
                else:
                    id = ctx.message.mentions[0].id
            
            if not self.fetch_gwen_sub(id, ctx.guild.id):
                await ctx.send('User is not subscribed to GwenBot.')
                return
            
            self.remove_from_gwen_sub(id, ctx.guild.id)
            self.logger.info(f'User {id} Server {ctx.guild.id} removed from GwenBot subscription by {ctx.author.id}.')
            await ctx.send('User removed from GwenBot subscription.')
        
        @self.command(name='blacklist', pass_context=True, aliases=['bl', 'Bl', 'BL'])
        @commands.has_permissions(kick_members=True)
        async def blacklist(ctx: commands.Context, id) -> None:
            """Command to add a user to the blacklist. Requires the user to have kick_members permissions."""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
            
            try:
                id = int(id)
            except ValueError:
                if len(ctx.message.mentions) == 0:
                    await ctx.send('Invalid id...', ephemeral=True)
                    return
                else:
                    id = ctx.message.mentions[0].id
            
            if not self.fetch_blacklist(id, ctx.guild.id):
                self.add_to_blacklist(id, ctx.guild.id)
                self.remove_from_gwen_sub(id, ctx.guild.id)
                await ctx.send('User successfully added to the Blacklist.')
                
                self.logger.info(f'User {id} Server {ctx.guild.id} added to Blacklist by {ctx.author.id}.')
            else:
                await ctx.send('User is already in blacklist.')
        
        @self.command(name='blremove', pass_context=True, aliases=['blr', 'blacklistremove'])
        @commands.has_permissions(kick_members=True)
        async def blremove(ctx: commands.Context, id) -> None:
            """Command to remove a user from the blacklist. Requires the user to have kick_members permissions."""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
        
            try:
                id = int(id)
            except ValueError:
                if len(ctx.message.mentions) == 0:
                    await ctx.send('Invalid id...', ephemeral=True)
                    return
                else:
                    id = ctx.message.mentions[0].id
            
            if self.fetch_blacklist(id, ctx.guild.id):
                self.remove_from_blacklist(id, ctx.guild.id)
                await ctx.send('User successfully removed from the Blacklist.')
                
                self.logger.info(f'User {id} Server {ctx.guild.id} removed from Blacklist by {ctx.author.id}.')
            else:
                await ctx.send('User is not Blacklisted.')
        
        @self.command(name='checkbl', pass_context=True, aliases=['check', 'checkblacklist'])
        async def checkbl(ctx: commands.Context, id=None) -> None:
            """Command to check if a user is blacklisted. +checkbl id[optional]"""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
            
            if id == None:
                if self.fetch_blacklist(ctx.author.id, ctx.guild.id):
                    await ctx.send('You are Blacklisted.')
                    return
                else:
                    await ctx.send('You are not Blacklisted.')
                    return

            try:
                id = int(id)
            except ValueError:
                if len(ctx.message.mentions) == 0:
                    await ctx.send('Invalid id...', ephemeral=True)
                    return
                else:
                    id = ctx.message.mentions[0].id
            
            if self.fetch_blacklist(id, ctx.guild.id):
                await ctx.send('User is Blacklisted.')
            else:
                await ctx.send('User is not Blacklisted.')
                
        #  To add any permissions command error:
        #  Add @commands.has_permissions(permissions) beforethe command. Then add:
        #  @command.error
        #  To this command.
        
        @quote.error
        @removesubmod.error
        @blremove.error
        @blacklist.error
        async def _error(ctx: commands.Context, error) -> None:
            """Run if a user does not have the permissions necessary to run a command."""
            
            if isinstance(error, commands.MissingPermissions):
                await ctx.send('You do not have the permissions to use this command.')
        
        
        #  These 2 commands make it so that the owner of the bot can always add and remove users from the blacklist.
        @self.command(pass_context=True)
        @commands.is_owner()
        async def fuckyou(ctx: commands.Context, id) -> None:
            """Alternative to +blacklist. Instead of permissions this requires the sender to be the owner of the bot.
            Change OWNER_ID in Config.config to your ID."""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
            
            try:
                id = int(id)
            except ValueError:
                if len(ctx.message.mentions) == 0:
                    await ctx.send('Invalid id...', ephemeral=True)
                    return
                else:
                    id = ctx.message.mentions[0].id

            if self.fetch_blacklist(id, ctx.guild.id):
                await ctx.send('User is already blacklisted.')
                return
            
            self.add_to_blacklist(id, ctx.guild.id)
            self.remove_from_gwen_sub(id, ctx.guild.id)
            
            await ctx.send('User added to the Blacklist.')
            
            self.logger.info(f'User {id} Server {ctx.guild.id} added to Blacklist by Owner.')
            
        
        @self.command(pass_context=True)
        @commands.is_owner()
        async def unfuckyou(ctx: commands.Context, id) -> None:
            """Alternative to +blremove. Instead of permissions this requires the sender to be the owner of the bot.
            Change OWNER_ID in Config.config to your ID."""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
                
            try:
                id = int(id)
            except ValueError:
                if len(ctx.message.mentions) == 0:
                    await ctx.send('Invalid id...', ephemeral=True)
                    return
                else:
                    id = ctx.message.mentions[0].id

            if not self.fetch_blacklist(id, ctx.guild.id):
                await ctx.send('User is not Blacklisted.')
                return
            
            self.remove_from_blacklist(id, ctx.guild.id)
            await ctx.send('User removed from the Blacklist.')
            
            self.logger.info(f'User {id} Server {ctx.guild.id} removed from Blacklist by Owner.')


        @self.command(pass_context=True)
        @commands.is_owner()
        async def fuckyouremove(ctx: commands.Context, id) -> None:
            """Removes a person from GwenSubs. Only usable by Owner."""
            
            if ctx.guild is None:
                await ctx.send('Command must be used in a server.')
                return
                
            try:
                id = int(id)
            except ValueError:
                if len(ctx.message.mentions) == 0:
                    await ctx.send('Invalid id...', ephemeral=True)
                    return
                else:
                    id = ctx.message.mentions[0].id
            
            if not self.fetch_gwen_sub(id, ctx.guild.id):
                await ctx.send('User is not subscribed to GwenBot.')
                return
            
            self.remove_from_gwen_sub(id, ctx.guild.id)
            await ctx.send('User removed from GwenBot subscription.')
            
        
        @self.command(pass_context=True)
        @commands.is_owner()
        async def shutdown(ctx: commands.Context) -> None:
            
            self.logger.critical('Bot was forcefully shut down.')
            
            await self.close()    

        @self.command(pass_context=True)
        @commands.is_owner()
        async def set_questions(ctx: commands.Context, amount: int) -> None:

            self.set_amount(amount)
            self.logger.info('Question amount was set.')

        @self.command(aliases=['cm'], pass_context=True)
        @commands.is_owner()
        async def count_messages(ctx: commands.Context):
            await ctx.send('Counting messages. This can take a while.')
            
            await self.check_amount()
            
            await ctx.send('Successfully counted the Messages.')
        
        @count_messages.error
        @set_questions.error
        @unfuckyou.error
        @fuckyou.error
        @fuckyouremove.error
        @shutdown.error
        async def _not_owner(ctx: commands.Context, error: Exception) -> None:
            if isinstance(error, commands.CheckFailure):
                await ctx.send('Who do you think you are...')
            

        #  All smaller/fun commands and any help-related command.

        #  Structure commands that send in DMs like this and change the message.
        @self.command(pass_context=True)
        async def list(ctx: commands.Context):
            user: discord.Member = ctx.message.author
            await user.send(', '.join(map(str,self.all_champions)))
        
        @self.command(pass_context=True)
        async def elolist(ctx: commands.Context):
            user: discord.Member = ctx.message.author
            await user.send(', '.join(map(str,self.elo_list)))
        
        #  Structure commands that send in the current chat like this and change the message.

        @self.command(aliases=['question', 'amount', 'qm', 'qms', 'questionmarks', 'questionmark', '?'])
        async def questions(ctx: commands.Context):
            await ctx.send(f'The current amount of question marks is {self.fetch_amount()[0][0]}.')


        @self.command(aliases=['question_user', 'amount_user', 'qm_user', 'qms_user', 'questionmarks_user', 'questionmark_user', '?_u', '?u'])
        async def questions_user(ctx: commands.Context, id):

            try:
                id = int(id)
            except ValueError:
                if len(ctx.message.mentions) == 0:
                    await ctx.send('Invalid id...', ephemeral=True)
                    return
                else:
                    id = ctx.message.mentions[0].id

            count = 0
            await ctx.send('Fetching the amount of question marks. This may take a while.')
            async for message in self.get_channel(MESSAGE_CHANNEL).history(limit=None):
                if message.author.id == id:
                    count += 1

            await ctx.send(f'The current amount of question marks by <@{id}> is {count}.')
            
        @self.command(aliases=['lb'])
        async def leaderboard(ctx: commands.Context):
            await ctx.send('Fetching the leaderboard. This may take a while.')
            user_dict: dict[int, int] = {}

            async for message in self.get_channel(MESSAGE_CHANNEL).history(limit=None):
                if not (message.author.id in user_dict.keys()):
                    user_dict[message.author.id] = 1
                else:
                    user_dict[message.author.id] += 1

            ordered_dict = {k: v for k, v in sorted(user_dict.items(), key=lambda item: item[1], reverse=True)}
            del user_dict

            user_list = []
            count = 0
            for key, value in ordered_dict.items():
                count += 1
                user_list.append([(await self.fetch_user(key)).display_name, value])

                if count >= 10:
                    break
            
            del ordered_dict
            await ctx.send(f"""1. {user_list[0][0]} with {user_list[0][1]} question marks sent.\n2. {user_list[1][0]} with {user_list[1][1]} question marks sent.\n3. {user_list[2][0]} with {user_list[2][1]} question marks sent.\n4. {user_list[3][0]} with {user_list[3][1]} question marks sent.\n5. {user_list[4][0]} with {user_list[4][1]} question marks sent.\n6. {user_list[5][0]} with {user_list[5][1]} question marks sent.\n7. {user_list[6][0]} with {user_list[6][1]} question marks sent.\n8. {user_list[7][0]} with {user_list[7][1]} question marks sent.\n9. {user_list[8][0]} with {user_list[8][1]} question marks sent.\n10. {user_list[9][0]} with {user_list[9][1]} question marks sent.""")
            
            del user_list
            gc.collect()

        @self.command(aliases=['Evasion', 'jax'])
        async def evasion(ctx: commands.Context):
            await ctx.send(r'Active: Jax enters Evasion, a defensive stance, for up to 2 seconds, causing all basic attacks against him to miss. Jax also takes 25% reduced damage from all champion area of effect abilities. After 1 second, Jax can reactivate to end it immediately.')
        
        @self.command(aliases=['gwen', 'immune'])
        async def g(ctx: commands.Context):
            if not self.fetch_gwen_sub(ctx.author.id, ctx.guild.id):
                return
            await ctx.send('Gwen is immune.')
        
        @self.command(aliases=['Aatrox'])
        async def aatrox(ctx: commands.Context):
            await ctx.send('Aatrox got ignited.')
        
        @self.command(aliases=['lh', 'Lh', 'LH'])
        async def listenhere(ctx: commands.Context):
            await ctx.send('listen here you little shit')
          
        @self.command(aliases=['Emo'])
        async def emo(ctx: commands.Context):
            await ctx.send("Aatrox's biggest fan (owns an Aatrox tshirt)")
            
        @self.command(aliases=['george','George','Sylas'])
        async def sylas(ctx: commands.Context):
            await ctx.send('Sylas pressed W. https://imgur.com/IHyk5hl')
            
        @self.command(aliases=['Version', 'checkver', 'patch'])
        async def version(ctx: commands.Context):
            await ctx.send(f'Currently on league patch {LOL_VERSION}.')
        
        #  Change the strings in helpmsg.py to edit the help messages.
        @self.command(aliases=['Menu', 'Help'])
        async def help(ctx: commands.Context):
            user: discord.Member = ctx.message.author
            await user.send(helpmsg)
        
        @self.command(aliases=['wrhelp'])
        async def winratehelp(ctx: commands.Context):
            user: discord.Member = ctx.message.author
            await user.send(wrhelpmsg)
            
        @self.command(aliases=['roles', 'role', 'rolelist'])
        async def role_list(ctx: commands.Context):
            user: discord.Member = ctx.message.author
            await user.send(', '.join(map(str,self.role_list)))

        @self.command(aliases=["Wis'adel", 'w', 'W', 'balans'])
        async def wisadel(ctx: commands.Context):
            await ctx.send(r"Immediately summons 2 Shadows of Revenant within attack range (max 3, persists after the skill ends); ATK +180%, attack interval increases significantly, ATK increases to 220% when attacking, splash damage radius expands, and 1st Talent activation chance increases to 100%. Skill activation grants 6 ammo and the skill ends when all ammo are used (Can manually deactivate skill)")

        

        @self.command()
        async def get_time(ctx: commands.Context):
            await ctx.send(f"current time is {datetime.datetime.now()} , times are {self.times[0]}")

        @self.command()
        async def lana(ctx: commands.Context):
            await ctx.send("https://media.discordapp.net/attachments/1320437220116791406/1321894179646734366/IMG_6786.png?ex=676ee564&is=676d93e4&hm=f7bb76b71252e93f59dfc8a6508dfbc8218b35775c332561cd8a68235a43fbfa&=&format=webp&quality=lossless&width=814&height=793")


        @self.command()
        async def zex(ctx: commands.Context):
            await ctx.send("https://media.discordapp.net/attachments/1320437220116791406/1338656615619887145/Screenshot_20250210_152123_Discord.jpg?ex=67abe0a0&is=67aa8f20&hm=27c2301565f3995aaec637387d3abf946d664bfa7880e7864215e5b266c21dad&=&format=webp")


        #  Deepseek reasoning integration
        
        async def gwenseekfunc(ctx: commands.Context, model: str, message: (str)) -> None:
            await ctx.send("Gwen is thinking...")
            response = ""
            message = ' '.join(map(str, message))
            
            full_messages = [{"role": "system", "content": "You are a helpful assistant. You are the champion 'Gwen' from League of Legends. Refer to yourself as 'Gwen'. Don't Roleplay too much as Gwen, just keep in mind that you are Gwen. The user is not Gwen. ALL replies must be 2000 or less characters in length."}]
            
            context_count: int = self.fetch_user_count_ds(ctx.message.author.id)[0]
            
            if context_count >= 5:
                self.delete_oldest_context_ds(ctx.message.author.id)
            
            previous_context = self.fetch_context_ds(ctx.message.author.id)

            for i in previous_context:
                full_messages.append({"role": "user", "content": i[2]})
                full_messages.append({"role": "assistant", "content":i[3]})

            full_messages.append({"role": "user", "content": message})
            
            response = await self.deepseek_client.chat.completions.create(
                model=f"deepseek-{model}",
                messages = full_messages,
                max_tokens=1024,
                temperature=0.7,
                stream=False
            )
            
            self.add_context_ds(ctx.message.author.id, message, response.choices[0].message.content)

            await ctx.send(response.choices[0].message.content + f"\n ||<@{ctx.message.author.id}>||")
            response = ""
            
            
        @self.command(aliases=["deepseek", "seek"])
        async def gwenseek(ctx: commands.Context, *message: (str)) -> None:
            await gwenseekfunc(ctx, "reasoner", message)
            
        @self.command(aliases=["deepseekbasic", "seekbasic", "gwenseekb"])
        async def gwenseekbasic(ctx: commands.Context, *message: (str)) -> None:
            await gwenseekfunc(ctx, "chat", message)
            
        @self.command(aliases=["ch", "clear"])
        async def clearhistory(ctx: commands.Context) -> None:
            self.clear_context_ds(ctx.message.author.id)
            await ctx.send("Cleared your Gwenseek history, snip snip!")

