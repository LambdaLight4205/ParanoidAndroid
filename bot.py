import discord
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
print("Lancement du bot")
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

def has_permission(user: discord.Member):
    return any(role.name in ["Admin", "King", "Rooks"] for role in user.roles)

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

bot.run(os.getenv('DISCORD_TOKEN'))