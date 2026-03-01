import logging

from config import BotConfig
from bot import ChessBot



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


if __name__ == "__main__":
    c: BotConfig = BotConfig()
    bot: ChessBot = ChessBot(c)
    bot.mainloop()