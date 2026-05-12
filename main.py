import sys
import threading
from time import sleep
from tkinter import ttk, Tk, Label
from tkextrafont import Font
from javascript import require, On
from configparser import ConfigParser

# ─── Config ───────────────────────────────────────────────────────────────────

CONFIG_PATH = "config.ini"
ADMINS = {"LambdaLight", "VeldtCocktail"}

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

# ─── Bot Logic ────────────────────────────────────────────────────────────────

class MinecraftBot:
    def __init__(self):
        self.bot = None
        self.jumping = False
        self._jump_thread = None
        self.auth_done = False

    def start(self):
        self.bot = mineflayer.createBot({
            "host": HOST,
            "port": PORT,
            "username": BOT_NAME,
            "respawn": AUTO_RESPAWN,
            "version": VERSION,
            "auth": "offline"
        })
        print(f"\033[32m[INFO] Connecting {BOT_NAME} to {HOST}:{PORT}...\033[0m")
        self._register_events()

    def stop(self):
        self.jumping = False
        if self.bot:
            self.bot.quit()
            self.bot = None
        print(f"\033[32m[INFO] Bot stopped.\033[0m")

    def _register_events(self):
        @On(self.bot, "login")
        def on_login(this):
            sleep(1)
            print(f"\033[32m[INFO] {BOT_NAME} connected!\033[0m")
            update_status("The bot is online")

        @On(self.bot, "messagestr")
        def on_msg(this, msg, *_):
            print("[SERVER]", msg)

        @On(self.bot, "spawn")
        def on_spawn(this):
            self.bot.chat(f"{BOT_NAME} connected!")
            update_status("The bot is online")

        @On(self.bot, "error")
        def on_error(this, err, *_):
            print(f"\033[31m[ERROR] Connection error: {err}\033[0m")
            on_disconnect()

        @On(self.bot, "kicked")
        def on_kicked(this, reason, *_):
            print(f"\033[31m[ERROR] Kicked: {reason}\033[0m")
            self.bot.end()
            on_disconnect()

        @On(self.bot, "messagestr")
        def on_msg(this, msg, *_):
            print("[SERVER]", msg)

            if self.auth_done:
                return

            msg = str(msg).lower()

            if "registerrequired" in msg or "/reg" in msg:
                sleep(1)
                self.bot.chat(BOT_REG)
                print(f"[INFO] Sent register command: {BOT_REG}")
                self.auth_done = True

            elif "loginrequired" in msg or "/login" in msg or "/l " in msg:
                sleep(1)
                self.bot.chat(BOT_LOGIN)
                print(f"[INFO] Sent login command: {BOT_LOGIN}")

            self.auth_done = True

        @On(self.bot, "chat")
        def on_chat(this, username, message, *_):
            if username == BOT_NAME:
                return
            if message.startswith("."):
                if username not in ADMINS:
                    self.bot.chat("You don't have enough permissions.")
                    return
                self._handle_command(username, message)

    def _handle_command(self, sender, message):
        cmd = message.split()[0].lower()
        args = message[len(cmd):].strip()

        if cmd == ".stop":
            self.jumping = False
            self.bot.clearControlStates()
            self.bot.chat(f"{sender} stopped the bot.")

        elif cmd == ".start":
            if not self.jumping:
                self.jumping = True
                self._jump_thread = threading.Thread(target=self._jump_loop, daemon=True)
                self._jump_thread.start()
                self.bot.chat(f"{sender} started alternating jumps!")

        elif cmd == ".command":
            if args:
                self.bot.chat(args)
            else:
                self.bot.chat("Usage: .command <command>")

        else:
            self.bot.chat(f"Unknown command: {cmd}")

    def _jump_loop(self):
        while self.jumping:
            self.bot.setControlState("jump", True)
            sleep(3)
            self.bot.setControlState("jump", False)
            sleep(3)


# ─── GUI ──────────────────────────────────────────────────────────────────────

mc_bot = MinecraftBot()

def update_status(text):
    bot_status.configure(text=text, font=("ebrima", 20))

def on_disconnect():
    update_status("The bot is offline")
    show_start_button()

def show_start_button():
    if "stop_button" in globals():
        stop_button.destroy()
    global start_button
    start_button = ttk.Button(root, text="Start", command=on_start_click)
    start_button.place(x=5, y=100, width=205)

def on_start_click():
    start_button.destroy()
    global stop_button
    stop_button = ttk.Button(root, text="Stop", command=on_stop_click)
    stop_button.place(x=5, y=100, width=205)
    threading.Thread(target=mc_bot.start, daemon=True).start()

def on_stop_click():
    mc_bot.stop()
    update_status("The bot is offline")
    show_start_button()

root = Tk()
Font(file="ebrima.ttf", family="ebrima")
bot_status = Label(root, text="The bot is offline", font=("ebrima", 20))

root.tk.call("source", "forest-dark.tcl")
root.title("")
root.geometry("215x150")
root.resizable(False, False)
ttk.Style().theme_use("forest-dark")

bot_status.place(x=5, y=30)

start_button = ttk.Button(root, text="Start", command=on_start_click)
start_button.place(x=5, y=100, width=205)

if sys.platform == "win32":
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)

root.mainloop()