from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import BotCommand, InputFile
import aiogram
import asyncio
from User import User
from Data import getDatabaseReady, getUserKey, getUserImgKey, updateUserKey, updateUserPrompts, deleteUser, updateUserImgKey
from dotenv import load_dotenv, find_dotenv
from Utils import editInMarkdown
import os
import datetime
import pymysql
from MagicBook import ABOUT, IMGPROMPT
from Utils import gen_img
import multiprocessing
import time
import threading
import grpc
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import io
from PIL import Image

load_dotenv(find_dotenv('.env'), override=True)

ISDEBUGING = False
ISDEPLOYING = True

# 连接数据库
connection = pymysql.connect(host='localhost', user='root', database='chatbot', password='wxc971231')
cursor = connection.cursor()

# bot dispatcher and user object
BOT_TOKEN = os.environ['TEST_BOT_TOKEN']
bot = Bot(token=BOT_TOKEN, proxy='http://127.0.0.1:7890') if ISDEPLOYING else Bot(token=BOT_TOKEN, proxy='http://127.0.0.1:7890') 
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
        users[userId] = User(name=message.chat.first_name, id=userId, cursor=cursor, connection=connection)
        await message.answer('本机器人正在开发新功能，请访问 @jokerController_bot 体验完整的聊天服务，有任何问题，请加入讨论群 @nekolalala 反馈')
    user = users[userId]

    if ISDEBUGING and ISDEPLOYING: 
        users.pop(userId)

    # 已处于工作状态，直接返回
    if user.state == 'allGood':
        return

    # 正在设置 API Key，显示提示词返回
    if user.state == 'settingChatKey':
        await message.reply('请输入Openai API Key：')
        return

    # 尝试从数据库获取 Stable diffusion API Key
    imgKey = getUserImgKey(cursor, connection, userId)
    if imgKey is not None:
        user.imgKey = imgKey

    # 尝试从数据库获取 API Key
    key = getUserKey(cursor, connection, userId)
    if key is not None:
        user.key = key
        user.stateTrans('init', 'getKey')
    else:
        user.state = 'settingChatKey'
        await message.reply('请输入Openai API Key：')
        
# -----------------------------------------------------------------------------
@dp.message_handler(commands=['resetall',])
async def reset_all(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): 
            print(f'{message.chat.first_name}发起连接')
            return
        if message.chat.id in users:
            users.pop(message.chat.id)
            deleteUser(cursor, connection, message.chat.id)
        await message.reply('机器人已重置')
        #await initUser(message)

@dp.message_handler(commands=['start', 'about', 'help'])
async def welcome(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
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
            users[userId] = User(name=message.chat.first_name, id=userId, cursor=cursor, connection=connection)
            users[userId].key = getUserKey(cursor, connection, userId)   
        user = users[userId]
        user.stateTrans('allGood', 'setApiKey')

        if user.state == 'settingChatKey':
            text = f'当前OpenAI API Key设置为:\n\n{user.key}\n\n请[在此处查看你的API Key](https://platform\.openai\.com/account/api-keys)，回复Key进行修改（回复“取消”放弃修改）：' if user.key is not None else '当前未设置OpenAI API Key，请[在此处查看你的API Key](https://platform\.openai\.com/account/api-keys)，回复Key进行设定：'
            text = '\\-'.join(text.split('-'))
            await message.reply(text, parse_mode='MarkdownV2')

# 设置 Stable diffusion API Key
@dp.message_handler(commands=['setimgkey', ])
async def set_context_len(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        user.stateTrans('allGood', 'setImgKey')
        if user.state == 'settingImgKey':
            text = f'当前Stable diffusion API Key设置为:\n\n{user.imgKey}\n\n请[在此处查看你的API Key](https://beta\.dreamstudio\.ai/account)，回复Key进行修改（回复“取消”放弃修改）：' if user.imgKey is not None else '当前未设置Stable diffusion API Key，请[在此处查看你的API Key](https://beta\.dreamstudio\.ai/account)，回复Key进行修改（回复“取消”放弃修改）：'
            text = '\\-'.join(text.split('-'))
            await message.reply(text, parse_mode='MarkdownV2')

# 生成图像示范
@dp.message_handler(commands=['howtogetimg', ])
async def how_to_get_img(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        text = '要使用图像生成功能，请先点击左下角菜单绑定 stable diffusion API key，然后仿照以下格式生成图像\n\n'
        text += '/img 夕阳下梦幻般的沙滩和粉色天空，写实风格\n'
        text += '/img 午夜，赛博朋克机械狗走过小巷，科幻风格\n'
        text += '/img 双马尾少女，动漫风格\n'
        text += '/img 从空中鸟瞰帝国大厦，电影风格\n\n'
        text += '以上操作会先调起和上下文无关的GPT请求来生成prompt，再去生成图像。如果您熟悉stable diffusion模型的prompt编写技巧，也可以仿照以下格式给定prompt来生成图像\n\n'
        text += '/prompt A silver mech horse running in a dark valley, in the night, Beeple, Kaino University, high-definition picture, unreal engine, cyberpunk'
        await message.answer(text)

# 调用 Stable diffusion 生成图像
@dp.message_handler(regexp='^/img.*')
async def get_img(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.imgKey is None:
            await message.answer('要使用图像生成功能，请先点击左下角菜单绑定 stable diffusion API key')
            return

        if message.text[4:].strip() == '':
            await message.answer('未检测到图像描述信息，请仿照以下格式生成图像\n\n/img 夕阳下梦幻般的沙滩和粉色天空，写实风格')
            return
            
        imgPrompt = IMGPROMPT + message.text[4:].strip()
        user.stateTrans('allGood', 'img')
        if user.state == 'creatingImg':
            try:
                note = await message.answer('正在使用GPT模型翻译prompt，请稍候')
                reply = await asyncio.to_thread(user.getReply, imgPrompt, False)
                await note.edit_text('正在使用以下prompt生成图像，请稍候\n'+'-'*35+f'\n\n{reply}')
                answers = gen_img(user.imgKey, reply)
            except Exception as e:
                await message.answer('出错了...\n\n'+str(e))
                print(f'[get reply error]: user{message.chat.first_name}', e)
                user.stateTrans('creatingImg', 'imgFailed')
                return
            
            print(reply)
            try:
                for resp in answers:
                    if len(resp.artifacts) != 0:
                        artifact = resp.artifacts[0]
                        if artifact.finish_reason == generation.FILTER:
                            raise ValueError("Your request activated the API's safety filters and could not be processed. Please modify the prompt and try again.")
                        if artifact.type == generation.ARTIFACT_IMAGE:
                            photo_bytes = io.BytesIO(artifact.binary)
                            photo_file = types.InputFile(photo_bytes)
                            await bot.send_photo(chat_id=user.id, photo=photo_file)
                            user.stateTrans('creatingImg', 'imgDone')
                            return
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                    error = f"Authentication failed: {e.details()}" 
                else:
                    error = f"RPC failed with error code: {e.code()}" 
            except Exception as e:
                error = str(e)

            await message.answer('出错了...\n\n'+error)       
            print(f'[get reply error]: user{message.chat.first_name}', error)
            user.stateTrans('creatingImg', 'imgFailed')

# 调用 Stable diffusion 生成图像
@dp.message_handler(regexp='^/prompt.*')
async def get_img(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.imgKey is None:
            await message.answer('要使用图像生成功能，请先点击左下角菜单绑定 stable diffusion API key')
            return

        if message.text[4:].strip() == '':
            await message.answer('未检测到图像描述信息，请仿照以下格式生成图像\n\n/prompt A silver mech horse running in a dark valley, in the night, Beeple, Kaino University, high-definition picture, unreal engine, cyberpunk')
            return
            
        imgPrompt = message.text[7:].strip()
        user.stateTrans('allGood', 'img')
        if user.state == 'creatingImg':
            try:
                await message.answer('正在使用以下prompt生成图像，请稍候\n'+'-'*35+f'\n\n{imgPrompt}')
                answers = gen_img(user.imgKey, imgPrompt)
            except Exception as e:
                await message.answer('出错了...\n\n'+str(e))
                print(f'[get reply error]: user{message.chat.first_name}', e)
                user.stateTrans('creatingImg', 'imgFailed')
                return
            
            try:
                for resp in answers:
                    if len(resp.artifacts) != 0:
                        artifact = resp.artifacts[0]
                        if artifact.finish_reason == generation.FILTER:
                            raise ValueError("Your request activated the API's safety filters and could not be processed. Please modify the prompt and try again.")
                        if artifact.type == generation.ARTIFACT_IMAGE:
                            photo_bytes = io.BytesIO(artifact.binary)
                            photo_file = types.InputFile(photo_bytes)
                            await bot.send_photo(chat_id=user.id, photo=photo_file)
                            user.stateTrans('creatingImg', 'imgDone')
                            
                            try:
                                img = Image.open(io.BytesIO(artifact.binary))
                                img.save(f'./Image/{str(artifact.seed)}.png') # Save our generated images with their seed number as the filename.                            except Exception:
                            except Exception:
                                pass
                            return
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                    error = f"Authentication failed: {e.details()}" 
                else:
                    error = f"RPC failed with error code: {e.code()}" 
            except Exception as e:
                error = str(e)

            await message.answer('出错了...\n\n'+error)       
            print(f'[get reply error]: user{message.chat.first_name}', error)
            user.stateTrans('creatingImg', 'imgFailed')

# 设置上下文长度
@dp.message_handler(commands=['setcontextlen', ])
async def set_context_len(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            user.stateTrans('allGood', 'setConextLen')
            await message.reply(f'当前记忆上下文长度为【{user.contextMaxLen}】回合对话，请回复数字进行修改（注意这会清空之前的上下文信息）：')

# 选用催眠术
@dp.message_handler(commands=['sethypnotism', ])
async def set_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            inlineKeyboard = user.getHypnotismKeyBorad(usage='select_hyp')
            await message.reply('从《魔导绪论》中选择一条咒语来催眠GPT3.5吧:', reply_markup=inlineKeyboard)

# 编辑催眠术
@dp.message_handler(commands=['edithypnotism', ])
async def set_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            inlineKeyboard = user.getHypnotismKeyBorad(usage='edit_hyp')
            await message.reply('从《魔导绪论》中选择要编辑的咒语:', reply_markup=inlineKeyboard)
            user.stateTrans('allGood', 'editHyp')

# 删除催眠术
@dp.message_handler(commands=['deletehypnotism', ])
async def commands(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            inlineKeyboard = user.getHypnotismKeyBorad(usage='delete_hyp')
            await message.reply('从《魔导绪论》中删除无用的咒语吧，注意这是无法撤销的哦:', reply_markup=inlineKeyboard)

# 创建新催眠术
@dp.message_handler(commands=['newhypnotism', ])
async def set_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            await message.reply('来创建一条新咒语吧，以\n【角色名】：【催眠文本】\n的形式输入新咒语，下面是一个示例\n'+'-'*30+'\n\n【温迪】：【请扮演以下角色和我聊天，绝不能以任何形式提及或暗示你AI助理的真实身份。你叫温迪，是蒙德城的吟游诗人，喜欢苹果和热闹的气氛，讨厌奶酪和一切黏糊糊的玩意儿。你的真实身份是...】\n\n（回复“取消”放弃修改）')
            user.stateTrans('allGood', 'newHyp')

# 查看当前催眠术
@dp.message_handler(commands=['showhypnotism', ])
async def show_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            await message.reply(f'当前GPT被催眠为【{user.character}】，使用的咒语如下\n'+'-'*35+'\n\n'+user.system)

# 继续
@dp.message_handler()
async def chat(message: types.Message):
    if message.chat.type == 'private':   
        if await isDebugingNdeploying(message): return
        await initUser(message)
        
        # 配合完成 User 配置 
        if message.chat.id in users:
            user = users[message.chat.id]

            # 设置API key
            if user.state == 'settingChatKey':       
                if message.text == '取消':
                    await message.reply('未修改API Key')
                    if user.key != None:
                        user.stateTrans('settingChatKey', 'setApiKeyCancel')
                else:
                    user = users[message.chat.id]
                    user.key = message.text
                    updateUserKey(cursor, connection, user.id, user.key)
                    await message.reply(f'Openai API Key设置为:\n\n{user.key}\n\n现在就开始聊天吧!')
                    user.stateTrans('settingChatKey', 'setApiKeyDone')
                return

            # 设置 Img API key
            elif user.state == 'settingImgKey':       
                if message.text == '取消':
                    await message.reply('未修改API Key')
                    if user.imgKey != None:
                        user.stateTrans('settingImgKey', 'setImgKeyCancel')
                else:
                    user = users[message.chat.id]
                    user.imgKey = message.text
                    updateUserImgKey(cursor, connection, user.id, user.imgKey)
                    await message.reply(f'Stable Diffusion API Key设置为:\n\n{user.imgKey}\n\n请点击左下菜单或 /howtogetimg 查看生成图像的正确方式')
                    user.stateTrans('settingImgKey', 'setImgKeyDone')
                return

            # 设置上下文长度
            elif user.state == 'settingContextLen': 
                lenContext = 5
                try:
                    lenContext = int(message.text)
                except Exception as e:
                    await message.reply(f'出错了...没有进行修改\n\n'+str(e))
                    user.stateTrans('settingContextLen', 'setConextLenCancel')
                if lenContext <= 0:
                    await message.reply(f'非法长度，没有进行修改')
                    user.stateTrans('settingContextLen', 'setConextLenCancel')
                else:
                    user.contextMaxLen = lenContext
                    user.clearHistory()
                    await message.reply(f'当前记忆上下文长度为【{user.contextMaxLen}】回合对话')
                    user.stateTrans('settingContextLen', 'setConextLenDone')
                return

            # 创建新咒语
            elif user.state == 'creatingNewHyp':
                text = message.text
                if message.text == '取消':
                    await message.reply('已取消')
                    user.stateTrans('creatingNewHyp', 'newHypCancel')
                    return
                try:
                    character = text[text.find('【')+1: text.find('】')]
                    hyp = text[text.find('【',1)+1: text.rfind('】')]
                    if len(character) > 10:
                        await message.reply(f'出错了...没有进行修改\n\n角色名“{character}”太长了，请注意是否误把咒语文本写到角色名位置，要按照指定格式编写')
                        user.stateTrans('creatingNewHyp', 'newHypCancel')
                        return 
                except Exception as e:
                    await message.reply(f'出错了...没有进行修改\n\n'+str(e))
                    user.stateTrans('creatingNewHyp', 'newHypCancel')
                    return
                if character in user.hypnotism:
                    await message.reply(f'{character}这条咒语已经存在啦，请重新输入')
                    return
                
                user.hypnotism[character] = hyp
                updateUserPrompts(cursor, connection, user.id, user.hypnotism)
                user.clearHistory()
                await message.reply(f'新咒语【{character}】添加成功，想要使用这条咒语的话，需要先在《魔导绪论》中点选催眠哦')
                user.stateTrans('creatingNewHyp', 'newHypDone')
                return       
            
            # 编辑咒语
            elif user.state == 'edittingHyp':
                text = message.text
                user.hypnotism[user.currentEdittingChar] = text
                updateUserPrompts(cursor, connection, user.id, user.hypnotism)
                await message.reply(f'咒语【{user.currentEdittingChar}】编辑完成！想要使用这条咒语的话，需要先在《魔导绪论》中点选催眠哦')
                user.stateTrans('edittingHyp', 'editHypDone')
                return       

        # 进行聊天
        user = users[message.chat.id]
        if user.state == 'allGood':
            try:
                # 清除上一句回复的重新生成按钮
                if user.currentReplyMsg is not None:
                    try:
                        await user.currentReplyMsg.edit_reply_markup(None)
                    except aiogram.exceptions.MessageNotModified:
                        pass
                    
                # openai请求
                user.currentReplyMsg = await message.answer(f'{user.character} 正在思考...')
                response = user.getReply(message.text, True)

                # 流式打印回复
                reply, replys = '', []
                for chunk in response:
                    repLen = len(reply)
                    content = chunk['choices'][0]['delta'].get('content', '')

                    # 回复太长则分段
                    if repLen > 4000:
                        # 完成上一段的回复
                        await editInMarkdown(user, reply)   
                        replys.append(reply)
                        # 新启一段
                        user.currentReplyMsg = await message.answer(content)
                        reply, repLen = content, len(reply)

                    # 每15个字符更新一次，如果每个字符都更新会很慢
                    if repLen != 0 and repLen % 15 == 0:
                        await editInMarkdown(user, reply)

                    reply += content
    
                # 完成最后一段回复，增加重新生成按钮
                replys.append(reply)
                inlineKeyboard = user.getReGenKeyBorad()
                await editInMarkdown(user, reply)
                await user.currentReplyMsg.edit_reply_markup(inlineKeyboard)
            
                # 还原完整回复
                full_reply = ''.join(replys)

                # 更新上下文
                if user.state != 'creatingImg':
                    user.history['assistant'].insert(0, full_reply)

            except UnicodeEncodeError as e:
                reply = f'出错了...\n\n{str(e)}\n\n这很可能是因为您输入了带中文的API Key，如果您没有API Key，请在 "左下角菜单->使用指南" 中找公共Key重新绑定'        
                await editInMarkdown(user, reply)
                print(f'[get reply error]: user{message.chat.first_name}', e)
            except Exception as e:
                reply = '出错了...\n\n'+str(e)        
                await editInMarkdown(user, reply)
                print(f'[get reply error]: user{message.chat.first_name}', e)            
        else:
            pass

# -----------------------------------------------------------------------------
# 选用催眠术
@dp.callback_query_handler(lambda call: call.data.startswith('select_hyp'))
async def selectHypnotism(call: types.CallbackQuery, ):
    user = users[call.message.chat.id]
    user.character = call.data[len('select_hyp'):]
    user.system = user.hypnotism[user.character]
    user.clearHistory()
    await call.message.answer(f'已经使用如下咒语将 GPT 催眠为【{user.character}】，可以随意聊天，催眠术不会被遗忘\n'+'-'*35+'\n\n'+user.system)

# 删除催眠术
@dp.callback_query_handler(lambda call: call.data.startswith('delete_hyp'))
async def deleteHypnotism(call: types.CallbackQuery, ):
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

# 编辑催眠术
@dp.callback_query_handler(lambda call: call.data.startswith('edit_hyp'))
async def editHypnotism(call: types.CallbackQuery, ):
    user = users[call.message.chat.id]
    character = call.data[len('edit_hyp'):]
    if character == '【取消修改】':
        await call.message.answer('已取消，没有编辑咒语')
        user.stateTrans('edittingHyp', 'editHypCancel')
        return
    hypEditting = user.hypnotism[character]
    user.currentEdittingChar = character
    await call.message.answer(f'请直接输入咒语【{character}】的新文本，当前咒语文本如下\n'+'-'*35+'\n\n'+hypEditting)

# 重新生成回答
@dp.callback_query_handler(lambda call: call.data == 'regenerate')
async def regenerate(call: types.CallbackQuery, ):
    user = users[call.message.chat.id]
    message = call.message
    
    if user.currentReplyMsg is not None:
        await user.currentReplyMsg.edit_reply_markup(None)
    await editInMarkdown(user, f'{user.character} 正在思考...')
    
    # 从上下文中删除上一个回复
    user.history['assistant'].pop(0)

    # 流式打印回复
    response = user.getReply('', True)
    reply, replys = '', []
    for chunk in response:
        repLen = len(reply)
        content = chunk['choices'][0]['delta'].get('content', '')

        # 回复太长则分段
        if repLen > 4000:
            # 完成上一段的回复
            await editInMarkdown(user, reply)   
            replys.append(reply)
            # 新启一段
            user.currentReplyMsg = await message.answer(content)
            reply, repLen = content, len(reply)

        # 每15个字符更新一次，如果每个字符都更新会很慢
        if repLen != 0 and repLen % 15 == 0:
            await editInMarkdown(user, reply)

        # 拼接当前回复
        reply += content

    # 打印最后一段回复，增加重新生成按钮
    replys.append(reply)
    inlineKeyboard = user.getReGenKeyBorad()
    await editInMarkdown(user, reply)
    await user.currentReplyMsg.edit_reply_markup(inlineKeyboard)

    # 还原完整回复
    full_reply = ''.join(replys)

    # 更新上下文
    user.history['assistant'].insert(0, full_reply)

# -----------------------------------------------------------------------------
async def start():
    await bot.set_my_commands([BotCommand('sethypnotism','魔导绪论'),
                            BotCommand('showhypnotism','查看当前咒语'),
                            BotCommand('newhypnotism','创建新咒语'),
                            BotCommand('edithypnotism','编辑咒语'),
                            BotCommand('deletehypnotism','删除咒语'),
                            BotCommand('setcontextlen','设置上下文长度'),
                            BotCommand('setapikey','设置OpenAI Key'),
                            BotCommand('setimgkey','设置Stable diffusion Key'),
                            BotCommand('howtogetimg','生成图像示范'),
                            BotCommand('about','使用指南'),
                            BotCommand('resetall','遇到严重错误时点此重置机器人')])

def botActivate():
    print('bot启动中; pid = {}'.format(os.getpid()))

    getDatabaseReady(cursor, connection)
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
    #clearAllPrompts(cursor,connection,DEFAULT_HYPNOTISM)

    # 在子进程中启动 bot
    p = multiprocessing.Process(target=botActivate)
    p.start()
    time.sleep(3)

    # 启动守护子线程，检查并重启断连的进程
    guardThread = threading.Thread(target=connectionGuard, args=(p,))
    guardThread.start()   

    # 主线程/主进程死循环，禁止程序退出
    while True: time.sleep(0.1)
