import sys
import threading
from time import sleep
from datetime import datetime
from tkinter import ttk, Tk, Label
from tkextrafont import Font
from javascript import require, On
from configparser import ConfigParser
from blessed import Terminal

# ─── Config ───────────────────────────────────────────────────────────────────

CONFIG_PATH = "config.ini"

config = ConfigParser()
config.read(CONFIG_PATH)

BOT_NAME     = config.get("bot", "name")
BOT_REG      = config.get("bot", "reg").strip('"')
BOT_LOGIN    = config.get("bot", "login").strip('"')
AUTO_RESPAWN = config.getboolean("bot", "auto_respawn")
HOST         = config.get("server", "host")
PORT         = config.getint("server", "port")
VERSION      = config.get("server", "version")

mineflayer = require("mineflayer")
term = Terminal()

# --- Utilities --- #
def current_time_str():
    now = datetime.now()
    hours, minutes, seconds = now.hour, now.minute, now.second
    return f"[{hours}:{minutes}:{seconds}] "

def infomsg(message):
    print(
        current_time_str() + term.green
        + "[INFO] " + message + term.normal
    )

def errormsg(message):
    print(
        current_time_str() + term.red
        + "[ERROR] " + message + term.normal
    )

def servermsg(message):
    print(
        current_time_str() + term.blue
        + "[SERVER] " + message + term.normal
    )


# ─── Bot Logic ───────────────────────────────────────────────────────────────

class MinecraftBot:
    def __init__(self, par):
        self.par = par
        self.active = False
        self.bot = None
        self.jumping = False
        self.jump_thread = None
        self.auth_done = False
        self.bot_threads_active = False

    def connect(self):
        if self.active:
            return

        self.bot = mineflayer.createBot({
            "host": HOST,
            "port": PORT,
            "username": BOT_NAME,
            "respawn": AUTO_RESPAWN,
            "version": VERSION,
            "auth": "offline"
        })

        self.register_events()
        
        infomsg(f"Connecting {BOT_NAME} to {HOST}:{PORT}...")

        self.bot_threads_active = False
        self.auth_done = False
        self.active = True
        self.bot_threads_active = True

        if self.jumping:
            self.jump_thread = threading.Thread(target=self.jump_loop, daemon=True)
            self.jump_thread.start()

    def disconnect(self):
        sleep(0.5)
        if self.active:
            try:
                self.bot.quit()
            except:
                pass

            self.active = False
            self.bot_threads_active = False

        infomsg("Bot stopped.")

    def register_events(self):
        @On(self.bot, "login")
        def on_login(this):
            infomsg(f"{BOT_NAME} connected !")

        @On(self.bot, "connect")
        def on_connect(this):
            infomsg("TCP connected.")

        @On(self.bot, "end")
        def on_end(this, *_):
            infomsg("Connection ended.")

        @On(self.bot, "spawn")
        def on_spawn(this):
            infomsg(f"{BOT_NAME} spawned !")

        @On(self.bot, "error")
        def on_error(this, err, *_):
            print(f"\033[31m[ERROR] Connection error: {err}\033[0m")
            self.disconnect()

            infomsg("Reconnecting in 5 seconds...")
            sleep(5)

            try:
                self.connect()
            except Exception as e:
                errormsg(str(e))

        @On(self.bot, "kicked")
        def on_kicked(this, reason, *_):
            print(f"\033[31m[ERROR] Kicked: {reason}\033[0m")
            self.disconnect()

            infomsg("Reconnecting in 5 seconds...")
            sleep(5)

            try:
                self.connect()
            except Exception as e:
                errormsg(str(e))

        @On(self.bot, "messagestr")
        def on_msg(this, msg, *_):
            msg = str(msg)
            servermsg(msg)

            lower_msg = msg.lower()

            if not self.auth_done:
                if "registerrequired" in lower_msg or "/reg" in lower_msg:
                    sleep(1)
                    self.bot.chat(BOT_REG)
                    print(f"[INFO] Sent register command: {BOT_REG}")
                    self.auth_done = True

                elif "loginrequired" in lower_msg or "/login" in lower_msg or "/l " in lower_msg:
                    sleep(1)
                    self.bot.chat(BOT_LOGIN)
                    print(f"[INFO] Sent login command: {BOT_LOGIN}")
                    self.auth_done = True


        @On(self.bot, "chat")
        def on_chat(this, username, message, *_):

            if message.startswith("!"):
                self.handle_command(username, message)

    def handle_command(self, sender, message):
        cmd = message.split()[0].lower()
        args = message[len(cmd):].strip()

        if cmd == "!jump":
            if not self.jumping:
                self.jumping = True
                self.jump_thread = threading.Thread(target=self.jump_loop, daemon=True)
                self.jump_thread.start()
                infomsg(f"{sender} started alternating jumps!")
                self.bot.chat(f"{sender} started alternating jumps!")

            else:
                self.jumping = False
                self.jump_thread = None
                infomsg(f"{sender} stopped alternating jumps!")
                self.bot.chat(f"{sender} stopped alternating jumps!")

        elif cmd == "!command":
            if args:
                self.bot.chat(args)
            else:
                self.bot.chat("Usage: !command <command>")

        elif cmd == "!sleep":
            infomsg("Disconnecting bot for 10s")
            threading.Thread(
                target=self.sleep_reconnect,
                daemon=True
            ).start()

        else:
            self.bot.chat(f"Unknown command: {cmd}")

    def jump_loop(self):
        while self.jumping:
            self.bot.setControlState("jump", True)
            sleep(3)
            self.bot.setControlState("jump", False)
            sleep(3)

    def sleep_reconnect(self):
        self.disconnect()

        infomsg("Reconnecting in 10 seconds...")
        sleep(10)

        try:
            self.connect()
        except Exception as e:
            errormsg(str(e))

# ─── GUI ─────────────────────────────────────────────────────────────────────

class Application:
    def __init__(self):
        self.bot_class = MinecraftBot(self)
        self.enabled = False

    def start(self):
        self.enabled = True
        self.console_chat_loop()


    def console_chat_loop(self):
        while self.enabled:
            try:
                msg = input().strip()
                cmd = msg.lower()

                if cmd.startswith("!start"):
                    if not self.bot_class.active:
                        self.bot_class.connect()
                        infomsg("Bot has been started")

                if cmd.startswith("!stop"):
                    if self.bot_class.active:
                        self.bot_class.disconnect()

                if cmd.startswith("!say"):
                    if len(msg) > 5:
                        self.bot_class.bot.chat(msg[5:])
                    else:
                        errormsg("Missing argument after <!say> command")

                if cmd.startswith("!goto"):
                    args = msg.split(' ')
                    pass
                    # TODO: implémenter le pathfinding pour se déplacer

            except EOFError:
                break

            except Exception as e:
                print(f"[ERROR] Console chat error: {e}")
        
if __name__ == "__main__":
    app = Application()
    app.start()