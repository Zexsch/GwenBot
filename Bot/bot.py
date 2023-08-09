import discord
import logging

from discord.ext import commands
from bs4 import BeautifulSoup
from requests import get as getreq
from requests.exceptions import RequestException
from json import loads as loadsjson
from random import randint
# from re import findall

# from .Database.database import Database
# from .Config.config import (LOL_VERSION, OWNER_ID, DEFAULT_CHANNEL, PREFIX)
from Database.database import Database
from .helpmsg import (helpmsg, wrhelpmsg)
from Config.config import (LOL_VERSION, OWNER_ID, DEFAULT_CHANNEL, PREFIX)

class Bot(commands.Bot, Database):
    def __init__(self):
        """
        Create an instance of the bot then do the run('TOKEN') command, replace TOKEN with your discord bot token. 
        League of Legends Gwen-themed discord bot. 
        Fetches the winrate of any given LOL champion via web scraping on u.gg 
        Also replies to any message containing 'Gwen' in any way [optional, opt-in] 
        Has some random fun commands. 
        """
        
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True
        
        commands.Bot.__init__(self, command_prefix=PREFIX, intents=intents, help_command=None, owner_id=OWNER_ID)
        
        self.response = getreq(f"https://ddragon.leagueoflegends.com/cdn/{LOL_VERSION}/data/en_US/champion.json")
        self.champion_json: dict[str, str] = loadsjson(self.response.text)
        self.elo_list: list[str] = ['overall', 'challenger', 'master', 'grandmaster', 'diamond', 'platinum', 'emerald',  
                                    'gold', 'silver', 'bronze', 'iron', 'diamond_2_plus', 'master_plus', 
                                    'diamond_plus', 'platinum_plus']
        
        # Alternative names for the elos to use in +wr.
        self.alternative_elos: dict[str, str] = {
            'platinum': ['platplus', 'plat+', 'platinumplus'],
            'diamond2': ['d2+', 'd2', 'd2plus', 'diamond2', 'diamond2plus', 'diamond2+', 'diamond_2plus', 'diamond_2+'],
            'diamond': ['d+', 'dplus', 'diamondplus'],
            'master': ['m+', 'master+', 'masterplus']
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
        
        
        self.create_db()
        
        self.add_commands()
    
    async def on_ready(self) -> None:
        self.logger.info('Bot enabled.')
    
    def alternative_elo_names(self, elo: str) -> str|str:
        if elo in self.alternative_elos.get('platinum'):
            return ('platinum_plus', 'plat+')
        elif elo in self.alternative_elos.get('diamond2'):
            return ('diamond_2_plus', 'd2+')
        elif elo in self.alternative_elos.get('diamond'): 
            return ('diamond_plus', 'd+')
        elif elo in self.alternative_elos.get('master'):
            return ('master_plus', 'master+')
        else:
            return (elo, elo)
        
    
    def fetch_wr_with_elo(self, champ: str, elo: str) -> float | None:
        r"""Return the winrate of a champion in a specified elo. Return :class:`None` if website is not reachable."""
        
        if elo == 'Platinum_plus':
            url = f'https://u.gg/lol/champions/{champ}/build'
        else:
            url = f'https://u.gg/lol/champions/{champ}/build?rank={elo}'
        
        try:
            web = getreq(url, headers={'User-Agent': 'Mozilla/5.0'}).content
        except RequestException:
            self.logger.error('Bot encountered an error when scraping u.gg.')
            return
        
        soup = BeautifulSoup(web, "html.parser")
        
        try:
            win_rate: str = soup.find_all('div', {'class':'value'})[1].text
        except IndexError:
            self.logger.error(f'Index out of range error in +wr elo. champ={champ}, elo={elo}, url={url}')
            return
        
        if not win_rate:
            self.logger.error("Winrate wasn't found.")
            return
        
        try:
            win_rate = float(win_rate.rstrip(win_rate[-1]))
        except ValueError:
            self.logger.error('Winrate fetched was not a float.')
            return
        
        try:
            match_count: str = soup.find_all('div', {'class':'value'})[5].text
        except IndexError:
            self.logger.error(f'Index out of range error in +wr elo match_count. champ={champ}, elo={elo}, url={url}')
            return
        
        return (win_rate, match_count)

    def fetch_wr_without_elo(self, champ: str) -> float | None:
        r"""Return the winrate of a champion without a specified elo. Return :class:`None` if website is not reachable."""
        
        url = f'https://u.gg/lol/champions/{champ}/build?rank=overall'
        
        try:
            web = getreq(url, headers={'User-Agent': 'Mozilla/5.0'}).content
        except RequestException:
            self.logger.error('Bot encountered an error when scraping u.gg.')
            return
        
        soup = BeautifulSoup(web, "html.parser")
        win_rate: str = soup.find_all('div', {'class':'value'})[1].text
        
        if not win_rate:
            self.logger.error("Winrate wasn't found.")
            return
        
        try:
            win_rate = float(win_rate.rstrip(win_rate[-1]))
        except ValueError:
            self.logger.error('Winrate fetched was not a float.')
            return
        
        try:
            match_count: str = soup.find_all('div', {'class':'value'})[5].text
        except IndexError:
            self.logger.error(f'Index out of range error in +wr elo match_count. champ={champ}, elo={elo}, url={url}')
            return
        
        return (win_rate, match_count)
        
    def add_commands(self) -> None:
        """Add all discord events, commands and listeners in this."""
        
        @self.listen('on_message')
        async def on_message(msg: discord.Message) -> None:
            """There can only be one on-message listener so you need to add all listen-related events in this function."""
            
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
        async def wr(ctx: commands.Context, champ: str, elo: str='', *args) -> None:
            """Make the bot send the winrate of a given champ in a specified elo. \n
            +wr (winrate) | (champion, r, random) (elo[optional]) \n
            Choosing r or random as a parameter will randomly select a champion from the list of all champions. \n
            Elo is optional.
            """
            
            champ: str = champ.capitalize()
            
            if elo != '':
                elo_tuple = self.alternative_elo_names(elo.lower())
                elo = elo_tuple[0]
            
            if elo != '' and elo not in self.elo_list:
                await ctx.send('Invalid elo. Check +elolist for a list of all accepted elos.')
                return
            
            if champ not in self.all_champions and (champ != 'R' or champ != 'Random'):
                await ctx.send('Invalid champion. Check +list for a list of all accepted champions.')
                return
            
            #  If elo is given
            if elo != '' and champ in self.all_champions:
                info = self.fetch_wr_with_elo(champ=champ, elo=elo)
                win_rate: float | None = info[0]
                
                if not win_rate:
                    await ctx.send('An error occured when fetching the winrate. Is u.gg down?')
                    return
                
                await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} with {info[1]} matches played.')
                return
            elif elo != '' and (champ == 'R' or champ == 'Random'):
                
                num: int = randint(0, len(self.all_champions)-1)
                champ: str = self.all_champions[num]
                
                info = self.fetch_wr_with_elo(champ=champ, elo=elo)
                win_rate: float | None = info[0]
                
                if not win_rate:
                    await ctx.send('An error occured when fetching the winrate. Is u.gg down?')
                    return
                
                await ctx.send(f'{champ} has a {win_rate}% winrate in {elo_tuple[1]} with {info[1]} matches played.')
                return
            
            #  If elo is not given
            if elo == '' and champ in self.all_champions:
                info = self.fetch_wr_without_elo(champ=champ)
                win_rate: float | None = info[0]
                
                if not win_rate:
                    await ctx.send('An error occured when fetching the winrate. Is u.gg down?')
                    return
                
                await ctx.send(f'{champ} has a {win_rate}% overall winrate with {info[1]} matches played.')
                return
            elif elo == '' and (champ == 'R' or champ == 'Random'):
                num: int = randint(0, len(self.all_champions)-1)
                champ: str = self.all_champions[num]
                
                info = self.fetch_wr_without_elo(champ=champ)
                win_rate: float | None = info[0]
                
                if not win_rate:
                    await ctx.send('An error occured when fetching the winrate. Is u.gg down?')
                    return
                
                await ctx.send(f'{champ} has a {win_rate}% overall winrate with {info[1]} matches played.')
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
                    await ctx.send('Invalid id...', ephemeral=True)
                    return
                
                if self.fetch_gwen_sub(id, ctx.guild.id):
                    await ctx.send('User is Subscribed.')
                else:
                    await ctx.send('User is not Subscribed.')
        
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
                await ctx.send('Invalid ID...', ephemeral=True)
                return
            
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
                await ctx.send('Invalid id...', ephemeral=True)
                return
            
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
                await ctx.send('Invalid id...', ephemeral=True)
                return
            
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
                await ctx.send('Invalid id...', ephemeral=True)
                return
            
            if self.fetch_blacklist(id, ctx.guild.id):
                await ctx.send('User is Blacklisted.')
            else:
                await ctx.send('User is not Blacklisted.')
                
        #  To add any permissions command error:
        #  Add @commands.has_permissions(permissions) beforethe command. Then add:
        #  @command.error
        #  To this command.
        
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
                await ctx.send('Invalid id...', ephemeral=True)
                return

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
                await ctx.send('Invalid id...', ephemeral=True)
                return

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
                await ctx.send('Invalid id...', ephemeral=True)
                return
            
            if not self.fetch_gwen_sub(id, ctx.guild.id):
                await ctx.send('User is not subscribed to GwenBot.')
                return
            
            self.remove_from_gwen_sub(id, ctx.guild.id)
            await ctx.send('User removed from GwenBot subscription.')
            
        
        @self.command(pass_context=True)
        @commands.is_owner()
        async def shutdown(ctx: commands.Context) -> None:
            
            self.logger.critical('Bot was forcefully shut down.')
            print('Bot forcefully shut down.')
            
            await self.close()    
              
        
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
            await ctx.send('Sylas pressed W.')
            
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
