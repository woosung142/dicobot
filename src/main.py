# import discord
# from discord.ext import commands

# # 1. 봇의 권한 설정 (매우 중요: 이게 없으면 메시지를 못 읽음)
# intents = discord.Intents.default()
# intents.message_content = True  # 메시지 내용 읽기 권한 허용

# # 2. 봇 객체 생성 (명령어 접두사는 '!')
# bot = commands.Bot(command_prefix='/', intents=intents)

# # 3. 봇이 켜졌을 때 실행할 이벤트
# @bot.event
# async def on_ready():
#     print(f'로그인 성공: {bot.user.name} (ID: {bot.user.id})')
#     print('봇이 준비되었습니다!')

# # 4. '!안녕' 이라고 치면 대답하는 명령어
# @bot.command()
# async def 안녕(ctx):
#     await ctx.send('반가워요! 저는 파이썬으로 만들어진 봇입니다.')
import discord
from discord.ext import commands
import json
import time
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

bot_key = os.getenv("DISCORD_BOT_KEY")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

WARN_FILE = "warnings.json"
RESET_SECONDS = 7 * 24 * 60 * 60  # 1주일

# ---------------- 데이터 로드 ----------------
def load_data():
    try:
        with open(WARN_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "last_reset": time.time()}

def save_data(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ---------------- 1주 리셋 ----------------
def check_reset():
    now = time.time()
    if now - data["last_reset"] >= RESET_SECONDS:
        data["users"] = {}
        data["last_reset"] = now
        save_data(data)

# ---------------- 봇 준비 ----------------
@bot.event
async def on_ready():
    print("봇 온라인!")

# ---------------- 메시지 처리 ----------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    check_reset()
    content = message.content

    # 경고 리스트
    if bot.user.mention in content and "경고 리스트" in content:
        if not data["users"]:
            await message.channel.send("📋 경고 받은 유저 없음")
            return

        text = "📋 **경고 리스트**\n"
        for uid, count in data["users"].items():
            member = message.guild.get_member(int(uid))
            if member:
                text += f"- {member.mention} : {count}회\n"

        await message.channel.send(text)
        return

    # 멘션된 유저가 있을 때만 처리
    if not message.mentions:
        return

    target = message.mentions[0]
    uid = str(target.id)
    data["users"].setdefault(uid, 0)

    # ---------------- 경고 지급 ----------------
    if "경고 지급되었습니다" in content:
        data["users"][uid] += 1
        count = data["users"][uid]
        save_data(data)

        await message.channel.send(
            f"⚠️ {target.mention} 경고 1회 지급\n현재 경고: **{count}회**"
        )

        if count >= 3:
            await message.channel.send(
                f"🚨 {target.mention} 경고 3회 누적!\n⏱ 타임아웃 3분 적용"
            )
            await target.timeout(timedelta(minutes=3))

    # ---------------- 경고 차감 ----------------
    if "경고 차감되었습니다" in content:
        data["users"][uid] = max(0, data["users"][uid] - 1)
        save_data(data)

        await message.channel.send(
            f"➖ {target.mention} 경고 1회 차감\n현재 경고: **{data['users'][uid]}회**"
        )

    await bot.process_commands(message)

# 5. 봇 실행 (아까 복사한 토큰을 여기에 붙여넣기)
bot.run(bot_key)