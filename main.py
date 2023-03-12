from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import BotCommand
import aiogram
import asyncio
from User import User, USER_STATUS_INIT, USER_STATUS_ALLGOOD, USER_STATUS_SETTINGKEY, USER_STATUS_SETTINGCONTEXT, USER_STATUS_NEWHYP
from Data import getDatabaseReady, getUserKey, updateUserKey, updateUserPrompts, deleteUser
from dotenv import load_dotenv, find_dotenv
import os
import pymysql
from MagicBook import ABOUT
import multiprocessing
import time
import threading
load_dotenv(find_dotenv('.env'), override=True)

ISDEBUGING = True
ISDEPLOYING = False

# 连接数据库
connection = pymysql.connect(host='localhost', user='root') if ISDEPLOYING else pymysql.connect(host='localhost', user='root', password='wxc971231')
cursor = connection.cursor()

# bot dispatcher and user object
BOT_TOKEN = os.environ['TEST_BOT_TOKEN'] if ISDEBUGING else os.environ['BOT_TOKEN']
bot = Bot(token=BOT_TOKEN) if ISDEPLOYING else Bot(token=BOT_TOKEN, proxy='http://127.0.0.1:7890') 
dp = Dispatcher(bot)    # 调度器 
users = {}              # 用户信息管理

# -----------------------------------------------------------------------------
async def isDebugingNdeploying(message):
    if ISDEPLOYING and ISDEBUGING:
        await message.reply('抱歉，正在维护中，请稍后访问...')
    return ISDEPLOYING and ISDEBUGING

async def initUser(message):
    # 建立 User 对象
    userId = message.chat.id 
    if userId not in users:
        print(f'新用户【{message.chat.first_name}】发起连接')
        users[userId] = User(id=userId, cursor=cursor, connection=connection)
    user = users[userId]

    # 已处于工作状态，直接返回
    if user.status == USER_STATUS_ALLGOOD:
        return

    # 正在设置 API Key，显示提示词返回
    if user.status == USER_STATUS_SETTINGKEY:
        await message.reply('请输入Openai API Key：')
        return

    # 尝试从数据库获取 API Key
    key = getUserKey(cursor, userId)
    if key is not None:
        user.key = key
        user.status = USER_STATUS_ALLGOOD
    else:
        user.status = USER_STATUS_SETTINGKEY
        await message.reply('请输入Openai API Key：')
        
# -----------------------------------------------------------------------------
@dp.message_handler(commands=['resetall',])
async def resetAll(message: types.Message):
    if message.chat.type == 'private':
        if message.chat.id in users:
            users.pop(message.chat.id)
            deleteUser(cursor, connection, message.chat.id)
        await message.reply('机器人已重置')
        #await initUser(message)

@dp.message_handler(commands=['start', 'about', 'help'])
async def welcome(message: types.Message):
    if message.chat.type == 'private':
        await message.answer(ABOUT, parse_mode='MarkdownV2', disable_web_page_preview=True)
        await initUser(message)

# 设置OpenAI API Key
@dp.message_handler(commands=['setapikey', ])
async def welcome(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        userId = message.chat.id 
        if userId not in users:
            print(f'新用户【{message.chat.first_name}】发起连接')
            users[userId] = User(id=userId, cursor=cursor, connection=connection)
            users[userId].key = getUserKey(cursor, userId)   
        users[userId].status = USER_STATUS_SETTINGKEY

        text = f'当前OpenAI API Key设置为:\n\n{users[userId].key}\n\n请回复新API Key进行修改（回复“取消”放弃修改）：' if users[userId].key is not None else '当前未设置OpenAI API Key，请回复API Key进行设定：'
        await message.reply(text)

# 设置上下文长度
@dp.message_handler(commands=['setcontextlen', ])
async def welcome(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.status == USER_STATUS_ALLGOOD:
            user.status = USER_STATUS_SETTINGCONTEXT
            await message.reply(f'当前记忆上下文长度为【{user.contextMaxLen}】回合对话，请回复数字进行修改（注意这会清空之前的上下文信息）：')

# 选用催眠术
@dp.message_handler(commands=['sethypnotism', ])
async def set_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.status == USER_STATUS_ALLGOOD:
            inlineKeyboard = user.getHypnotismKeyBorad(usage='select_hyp')
            await message.reply('从《魔导绪论》中选择一条咒语来催眠GPT3.5吧:', reply_markup=inlineKeyboard)

# 删除催眠术
@dp.message_handler(commands=['deletehypnotism', ])
async def commands(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.status == USER_STATUS_ALLGOOD:
            inlineKeyboard = user.getHypnotismKeyBorad(usage='delete_hyp')
            await message.reply('从《魔导绪论》中删除无用的咒语吧，注意这是无法撤销的哦:', reply_markup=inlineKeyboard)

# 创建新催眠术
@dp.message_handler(commands=['newhypnotism', ])
async def set_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.status == USER_STATUS_ALLGOOD:
            await message.reply('来创建一条新咒语吧，以\n【角色名】：【催眠文本】\n的形式输入新咒语，下面是一个示例\n'+'-'*30+'\n\n【温迪】：【请扮演以下角色和我聊天，绝不能以任何形式提及或暗示你AI助理的真实身份。你叫温迪，是蒙德城的吟游诗人，喜欢苹果和热闹的气氛，讨厌奶酪和一切黏糊糊的玩意儿。你的真实身份是...】\n\n（回复“取消”放弃修改）')
            user.status = USER_STATUS_NEWHYP

# 查看当前催眠术
@dp.message_handler(commands=['showhypnotism', ])
async def show_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.status == USER_STATUS_ALLGOOD:
            await message.reply(f'当前GPT被催眠为【{user.character}】，使用的咒语如下\n'+'-'*35+'\n\n'+user.system)

# 继续
@dp.message_handler()
async def chat(message: types.Message):
    if message.chat.type == 'private':   
        if await isDebugingNdeploying(message): return
        # 配合完成 User 配置 
        if message.chat.id in users:
            user = users[message.chat.id]
            if user.status == USER_STATUS_SETTINGKEY:       # 设置API key
                if message.text == '取消':
                    await message.reply('未修改API Key')
                    user.status = USER_STATUS_ALLGOOD if user.key != None else USER_STATUS_INIT
                else:
                    user = users[message.chat.id]
                    user.key = message.text
                    updateUserKey(cursor, connection, user.id, user.key)
                    await message.reply(f'Openai API Key设置为:\n\n{user.key}\n\n现在就开始聊天吧!')
                    user.status = USER_STATUS_ALLGOOD
                return
            elif user.status == USER_STATUS_SETTINGCONTEXT: # 设置上下文长度
                try:
                    contextLen = int(message.text)
                except Exception as e:
                    await message.reply(f'出错了...没有进行修改\n\n'+str(e))
                    user.status = USER_STATUS_ALLGOOD
                if contextLen <= 0:
                    await message.reply(f'非法长度，没有进行修改')
                    user.status = USER_STATUS_ALLGOOD
                else:
                    user.contextMaxLen = contextLen
                    user.clearHistory()
                    await message.reply(f'当前记忆上下文长度为【{user.contextMaxLen}】回合对话')
                    user.status = USER_STATUS_ALLGOOD
                return
            elif user.status == USER_STATUS_NEWHYP:
                text = message.text
                if message.text == '取消':
                    await message.reply('已取消')
                    user.status = USER_STATUS_ALLGOOD
                    return
                try:
                    character = text[text.find('【')+1: text.find('】')]
                    hyp = text[text.find('【',1)+1: text.rfind('】')]
                except Exception as e:
                    await message.reply(f'出错了...没有进行修改\n\n'+str(e))
                    user.status = USER_STATUS_ALLGOOD
                    return
                if character in user.hypnotism:
                    await message.reply(f'{character}这条咒语已经存在啦，请重新输入')
                    return
                
                user.hypnotism[character] = hyp
                updateUserPrompts(cursor, connection, user.id, user.hypnotism)
                user.clearHistory()
                await message.reply(f'新咒语【{character}】添加成功')
                user.status = USER_STATUS_ALLGOOD
                return

        # User初始化
        await initUser(message)

        # 进行聊天
        user = users[message.chat.id]
        if user.status == USER_STATUS_ALLGOOD:
            try:
                print(f'{message.chat.first_name}发起了API请求')
                reply = await asyncio.to_thread(users[message.chat.id].getReply, message.text)
            except Exception as e:
                reply = '出错了...\n\n'+str(e)        
                print(f'[get reply error]: user{message.chat.first_name}', e)
            try:
                await message.answer(reply)
            except aiogram.utils.exceptions.MessageIsTooLong:
                while len(reply) > 4000:
                    await message.answer(reply[:4000])
                    reply = reply[4000:]
                await message.answer(reply)
        else:
            pass

# -----------------------------------------------------------------------------
@dp.callback_query_handler(lambda call: call.data.startswith('select_hyp'))
async def selectHypnotism(call: types.CallbackQuery, ):
    user = users[call.message.chat.id]
    user.character = call.data[len('select_hyp'):]
    user.system = user.hypnotism[user.character]
    user.clearHistory()
    await call.message.answer(f'已经使用如下咒语将 GPT 催眠为【{user.character}】，可以随意聊天，催眠术不会被遗忘\n'+'-'*35+'\n\n'+user.system)

@dp.callback_query_handler(lambda call: call.data.startswith('delete_hyp'))
async def selectHypnotism(call: types.CallbackQuery, ):
    character = call.data[len('delete_hyp'):]
    if character == '【取消修改】':
        await call.message.answer('已取消，没有删除咒语')
        return
    user = users[call.message.chat.id]
    hypDeleted = user.hypnotism[character]
    user.hypnotism.pop(character)
    updateUserPrompts(cursor, connection, user.id, user.hypnotism)
    user.clearHistory()
    await call.message.answer(f'已将咒语【{character}】删除，原文为如下\n'+'-'*35+'\n\n'+hypDeleted)

# -----------------------------------------------------------------------------
async def start():
    await bot.set_my_commands([BotCommand('sethypnotism','魔导绪论'),
                            BotCommand('showhypnotism','查看当前咒语'),
                            BotCommand('newhypnotism','创建新咒语'),
                            BotCommand('deletehypnotism','删除咒语'),
                            BotCommand('setcontextlen','设置上下文长度'),
                            BotCommand('setapikey','设置OpenAI Key'),
                            BotCommand('about','使用指南'),
                            BotCommand('resetall','遇到严重错误时点此重置机器人')])

def botActivate():
    print('bot启动中; pid = {}'.format(os.getpid()))

    getDatabaseReady(cursor)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_until_complete(executor.start_polling(dp))

def connectionGuard(process):
    '''
    主进程守护线程在此检查bot进程是否死亡，并自动重启
    '''
    while True:
        if not process.is_alive():
            process = multiprocessing.Process(target=botActivate) 
            process.start()
        time.sleep(3)

if __name__ == '__main__':
    # 在子进程中启动 bot
    p = multiprocessing.Process(target=botActivate)
    p.start()
    time.sleep(3)

    # 启动守护子线程，检查并重启断连的进程
    guardThread = threading.Thread(target=connectionGuard, args=(p,))
    guardThread.start()   

    # 主线程/主进程死循环，禁止程序退出
    while True: time.sleep(0.1)