from Bot.bot import Bot
from Config.config import TOKEN

if __name__ == '__main__':
    bot = Bot()
    bot.run(TOKEN)