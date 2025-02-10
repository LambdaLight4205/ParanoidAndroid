import discord
import os
import json
from dotenv import load_dotenv
from discord.ext import commands

def default_config(id, cfg):
    if not id in cfg:
        cfg[id] = {
            'roles': ['Admin']
        }
        save_server_config(cfg)

    return cfg

def has_permission(user: discord.Member):
    global config
    server_id = user.guild.id
    config = default_config(server_id, config)

    allowed_roles = config[server_id]['roles']

    print(f"Permission test : {user.name} with roles {user.roles} from guild {server_id}")
    return any(role.name in allowed_roles for role in user.roles)

def get_admin_roles(server_id):
    return config[server_id]['roles']

def get_server_config():
    with open("config.json", "r") as file:
        content = json.load(file)

    return content

def save_server_config(cfg):
    with open("config.json", "w") as file:
        json.dump(cfg, file, indent=4)

load_dotenv()
config = get_server_config()

print("Lancement du bot")
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot allumé !")
    try:
        synced = await bot.tree.sync()
        print(f"Commands synchronisées : {len(synced)}")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message: discord.Message):
    channel = message.channel
    content = message.content
    author = message.author

    if message.author.bot:
        return

    if content.lower() == "bonjour":
        await channel.send(f"Salut {author} !")

@bot.tree.command(name="github", description="Lien du GitHub de LambdaLight")
async def github(interaction: discord.Interaction):
    await interaction.response.send_message("Voici le lien de mon GitHub : https://github.com/LambdaLight4205/ParanoidAndroid\nN'hésite pas à contribuer !")

@bot.tree.command(name="creator", description="Informations à propos du créateur du bot")
async def creator(interaction: discord.Interaction):
    embed = discord.Embed(
        title="LambdaLight",
        description="LambdaLight c'est le génie qui m'a codé ;-)",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="warn", description="Alerter un utilisateur")
async def warn(interaction: discord.Interaction, member: discord.Member):
    if not has_permission(interaction.user):
        await interaction.response.send_message("Vous n'avez pas la permission d'utiliser cette commande", ephemeral=True)
        return

    await member.send("Tu as reçu un warn")
    await interaction.response.send_message("Alerte envoyée", ephemeral=True)

@bot.tree.command(name="ban", description="Bannir un utilisateur")
async def ban(interaction: discord.Interaction, member: discord.Member):
    if not has_permission(interaction.user):
        await interaction.response.send_message("Vous n'avez pas la permission d'utiliser cette commande", ephemeral=True)
        return
    
    await interaction.response.send_message(f"{member} a été banni")
    await member.ban(reason="Tu as été banni définitivement")

@bot.tree.command(name="configure", description="Configuer le bot")
async def configure(interaction: discord.Interaction, category: str, action: str = None, value: str = None):
    if not has_permission(interaction.user):
        await interaction.response.send_message("Vous n'avez pas la permission d'utiliser cette commande", ephemeral=True)
        return
    
    if category and category == 'roles':
        if action and action == 'list':
            liste_roles = get_admin_roles(interaction.guild_id)
            await interaction.response.send_message(f'Liste des rôles ayant des permissions : {liste_roles}')
            return

    await interaction.response.send_message(f'Arguments invalides pour la configuration')

bot.run(os.getenv('DISCORD_TOKEN'))