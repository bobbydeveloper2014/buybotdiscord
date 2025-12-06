import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

load_dotenv()  # Load biến môi trường từ .env
TOKEN = os.getenv("DISCORD_TOKEN")
ROLE_NAME = "Contribute"
CONFIG_FILE = "buybot_config.json"

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

class ConfirmBuy(ui.View):
    def __init__(self, user_id, product_name):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.product_name = product_name

    @ui.button(label="Đồng ý mua", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Bạn không được click nút này!", ephemeral=True)
            return
        role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"Bạn đã được gán role {ROLE_NAME} vì là người mua! Và bạn hãy ủng hộ shop của chúng tôi trong lần tiếp theo nhé.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(f"Role {ROLE_NAME} không tồn tại!", ephemeral=True)
        guild_id = str(interaction.guild.id)
        channel_id = config.get(guild_id, {}).get("log_channel")
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                await channel.send(f"✅ **{interaction.user.mention}** đã mua: **{self.product_name}**")
        self.stop()

@bot.event
async def on_ready():
    print(f"Bot đang chạy: {bot.user}")
    for guild in bot.guilds:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"Synced commands cho guild: {guild.name} ({guild.id})")

@bot.tree.command(name="setupbuybot", description="Chọn channel để bot thông báo khi có người mua")
@app_commands.describe(channel="Chọn channel để nhận thông báo")
async def setupbuybot(interaction: discord.Interaction, channel: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id]["log_channel"] = channel.id
    save_config()
    await interaction.response.send_message(
        f"✅ Channel {channel.mention} đã được setup làm nơi nhận thông báo!", ephemeral=True
    )

@bot.tree.command(name="buy", description="Xác nhận mua để nhận role")
@app_commands.describe(product="Nhập tên sản phẩm bạn muốn mua")
async def buy(interaction: discord.Interaction, product: str):
    await interaction.response.send_message(
        f"Bạn xác nhận muốn mua: **{product}**? Nhấn nút bên dưới để nhận role.",
        view=ConfirmBuy(interaction.user.id, product),
        ephemeral=True
    )

# ====== Keep alive trực tiếp trong main.py ======
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()

bot.run(TOKEN)