import logging
import threading

from core.config import Config
from bot import DesktopBot, RemotePhoneBot
from desktop.gui import GUI



logger = logging.getLogger(__name__)

class App:
    def __init__(self):
        self.bot = None
        self.bot_thread = None
        self.config = Config()
        self.gui = None

    def stop_bot(self):
        """Safely shuts down the currently running bot and closes its thread."""
        if self.bot and self.bot.running:
            logging.info("Stopping current bot...")
            self.bot.stop()
            
            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join(timeout=2)
            
            logging.info("Bot successfully stopped.")

    def start_bot(self):
        """Creates a completely fresh bot instance and starts it in a background thread."""
        # Ensure any old bot is fully stopped
        self.stop_bot()
        
        # Re-instantiate bot entirely -> guarantee a fresh board
        bot_mode = self.config.mode
        if bot_mode == "Remote Phone":
            self.bot = RemotePhoneBot(self.config)
        else:
            self.bot = DesktopBot(self.config)
            
        # Start new background thread
        logging.info(f"Starting {bot_mode} Bot...")
        self.bot_thread = threading.Thread(target=self.bot.mainloop, daemon=True)
        self.bot_thread.start()

    def run(self):
        self.gui = GUI(
            config=self.config,
            start_cmd=self.start_bot,
            stop_cmd=self.stop_bot
        )

        self.gui.run()
        self.stop_bot()