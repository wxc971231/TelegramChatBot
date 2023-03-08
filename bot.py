from tkinter import Button
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import BotCommand
import random
import asyncio
from utils import User
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv('.env'), override=True)
BOT_TOKEN = os.environ['BOT_TOKEN']
KEY = os.environ['MY_OPENAI_KEY']

bot = Bot(token=BOT_TOKEN, proxy='http://127.0.0.1:7890')       # 通过代理连接
dp = Dispatcher(bot)                                            # 调度器 
users = {}

@dp.message_handler(commands=['start', 'help'])
async def welcome(message: types.Message):
    await message.reply('机器人已启动，即刻发送信息开始聊天吧')

@dp.message_handler(commands=['newhypnotism', 'edithypnotism', 'deletehypnotism'])
async def commands(message: types.Message):
    if message.chat.type == 'private' and message.chat.id not in users:
        print(f'新用户【{message.chat.first_name}】发起连接')
        users[message.chat.id] = User(KEY)

@dp.message_handler(commands=['sethypnotism', ])
async def set_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if message.chat.id not in users:
            print(f'新用户【{message.chat.first_name}】发起连接')
            users[message.chat.id] = User(KEY)
            
        user = users[message.chat.id]
        inlineKeyboard = user.getHypnotismKeyBorad()
        await message.reply('从《魔导绪论》中选择一条咒语来催眠GPT3.5吧:', reply_markup=inlineKeyboard)

@dp.message_handler(commands=['showhypnotism', ])
async def show_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if message.chat.id not in users:
            print(f'新用户【{message.chat.first_name}】发起连接')
            users[message.chat.id] = User(KEY)
        
        user = users[message.chat.id]
        await message.answer(f'当前 GPT 被催眠为【{user.character}】，使用的咒语如下\n'+'-'*35+'\n\n'+user.system)

@dp.message_handler()
async def welcome(message: types.Message):
    if message.chat.type == 'private' and message.chat.id not in users:
        print(f'新用户【{message.chat.first_name}】发起连接')
        users[message.chat.id] = User(KEY)

    try:
        print(f'{message.chat.first_name}发起了API请求')
        reply = users[message.chat.id].getReply(message.text)
    except Exception as e:
        reply = '出错了...\n\n'+str(e)        
        print(f'[get reply error]: user{message.chat.first_name}', e)
    
    await message.answer(reply)

# ----------------------------------------------------------------------------------------
@dp.callback_query_handler()
async def selectHypnotism(call: types.CallbackQuery):
    user = users[call.message.chat.id]
    user.character = call.data
    user.system = user.hypnotism[user.character]
    user.clearHistory()

    await call.message.answer(f'已经使用如下咒语将 GPT 催眠为【{user.character}】\n'+'-'*35+'\n\n'+user.system)


async def start():
    await bot.set_my_commands([BotCommand('sethypnotism','魔导绪论'),
                            BotCommand('showhypnotism','查看当前咒语'),
                            BotCommand('newhypnotism','创建新咒语'),
                            BotCommand('edithypnotism','编辑咒语'), 
                            BotCommand('deletehypnotism','删除咒语'),
                            BotCommand('setcontextlen','设置上下文长度')])

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_until_complete(executor.start_polling(dp))
               
