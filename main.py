import logging

from config import Config
from bot import ChessBot



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


if __name__ == "__main__":
    c: Config = Config()
    bot: ChessBot = ChessBot(c)
    bot.mainloop()