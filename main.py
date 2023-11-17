from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import BotCommand
import aiogram
import asyncio
from User import User
from Data import getDatabaseReady, getUserKey, getUserImgKey, updateUserKey, updateUserPrompts, deleteUser, updateUserImgKey
from dotenv import load_dotenv, find_dotenv
from Utils import editInMarkdown
import os
import pymysql
from MagicBook import ABOUT, IMGPROMPT, HOW_TO_GET_IMG, NEW_HYPNOTISM
from Utils import gen_img
import multiprocessing
import time
import threading
import grpc
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import io
import openai
import warnings
from PIL import Image

load_dotenv(find_dotenv('.env'), override=True)

ISDEBUGING = False
ISDEPLOYING = True

# 连接数据库
connection = pymysql.connect(host='localhost', user='root', database='chatbot', password='wxc971231')
cursor = connection.cursor()

# proxy setting for openai API
os.environ['http_proxy'] = '127.0.0.1:15732'
os.environ['https_proxy'] = '127.0.0.1:15732'

# bot dispatcher and user object
BOT_TOKEN = os.environ['TEST_BOT_TOKEN']
bot = Bot(token=BOT_TOKEN, proxy='http://127.0.0.1:15732') if ISDEPLOYING else Bot(token=BOT_TOKEN, proxy='http://127.0.0.1:15732') 
dp = Dispatcher(bot)    # 调度器 
users = {}              # 用户信息管理

# -----------------------------------------------------------------------------
async def isDebugingNdeploying(message):
    if ISDEPLOYING and ISDEBUGING:
        await message.reply('抱歉，正在维护中，请稍后访问...')
    return ISDEPLOYING and ISDEBUGING

async def initUser(message, typing=False):
    # 建立 User 对象
    userId = message.chat.id 
    if userId not in users:
        print(f'新用户【{message.chat.first_name}】发起连接')
        users[userId] = User(name=message.chat.first_name, id=userId, cursor=cursor, connection=connection)
        await message.answer('机器人维护导致丢失了上下文记忆，非常抱歉，欢迎大家加入讨论群 @nekolalala')
    user = users[userId]

    if ISDEBUGING and ISDEPLOYING: 
        users.pop(userId)

    # 已处于工作状态，直接返回
    if user.state == 'allGood':
        return

    # 正在设置 API Key，显示提示词返回
    if user.state == 'settingChatKey' and not typing:
        await message.reply('请输入Openai API Key，可在[Openai官网](https://platform\.openai\.com/account/api\-keys) 查看：',parse_mode='MarkdownV2', disable_web_page_preview=True)
        return

    # 尝试从数据库获取 Stable diffusion API Key
    imgKey = getUserImgKey(cursor, connection, userId)
    if imgKey is not None:
        user.imgKey = imgKey

    # 尝试从数据库获取 API Key
    key = getUserKey(cursor, connection, userId)
    if key is not None:
        user.setOpenAIKey(key)
        user.stateTrans('init', 'getKey')
    else:
        user.state = 'settingChatKey'
        if not typing:
            await message.reply('请输入Openai API Key，可在[Openai官网](https://platform\.openai\.com/account/api\-keys) 查看：',parse_mode='MarkdownV2', disable_web_page_preview=True)
        
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
async def set_openai_key(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        userId = message.chat.id 
        if userId not in users:
            print(f'新用户【{message.chat.first_name}】发起连接')
            users[userId] = User(name=message.chat.first_name, id=userId, cursor=cursor, connection=connection)
            users[userId].setOpenAIKey(getUserKey(cursor, connection, userId))
        user = users[userId]
        user.stateTrans('allGood', 'setApiKey')

        if user.state == 'settingChatKey':
            text = f'当前OpenAI API Key设置为:\n\n`{user.key}`\n\n请[在此处查看你的API Key](https://platform.openai.com/account/api-keys)，回复Key进行修改' if user.key is not None else '当前未设置OpenAI API Key，请[在此处查看你的API Key](https://platform.openai.com/account/api-keys)，回复Key进行设定：'
            text = text.replace('-', r'\-').replace('.', r'\.')            
            await message.answer(
                text, parse_mode='MarkdownV2', 
                reply_markup=user.getCancelBorad()
            )


# 设置 Stable diffusion API Key
@dp.message_handler(commands=['setimgkey', ])
async def set_img_key(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        user.stateTrans('allGood', 'setImgKey')
        if user.state == 'settingImgKey':
            text = f'当前Stable diffusion API Key设置为:\n\n`{user.imgKey}`\n\n请[在此处查看你的API Key](https://beta.dreamstudio.ai/account)，回复Key进行修改' if user.imgKey is not None else '当前未设置Stable diffusion API Key，请[在此处查看你的API Key](https://beta.dreamstudio.ai/account)，回复Key进行修改：'
            text = text.replace('-', r'\-').replace('.', r'\.')
            await message.answer(
                text, parse_mode='MarkdownV2', 
                reply_markup=user.getCancelBorad()
            )

# 生成图像示范
@dp.message_handler(commands=['howtogetimg', ])
async def how_to_get_img(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        await message.answer(HOW_TO_GET_IMG, parse_mode='MarkdownV2')

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
                    for artifact in resp.artifacts:
                        if artifact.finish_reason == generation.FILTER:
                            warnings.warn(
                                "Your request activated the API's safety filters and could not be processed."
                                "Please modify the prompt and try again.")
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
                    for artifact in resp.artifacts:
                        if artifact.finish_reason == generation.FILTER:
                            warnings.warn(
                                "Your request activated the API's safety filters and could not be processed."
                                "Please modify the prompt and try again.")
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

# 选择模型
@dp.message_handler(commands=['setmodel', ])
async def set_model(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            await message.reply(
                '选择对话使用的模型，注意只有*绑定支付方式且有过支付历史*的账户才能使用GPT4，可以在[这里](https://platform\.openai\.com/account/billing/history)查看您的账户是否有支付历史', 
                reply_markup=user.getModelKeyBorad(),
                parse_mode='MarkdownV2'
            )

# 选用催眠术
@dp.message_handler(commands=['sethypnotism', ])
async def set_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            await message.reply(
                '从《魔导绪论》中选择一条咒语来催眠 GPT 模型吧:', 
                reply_markup=user.getHypnotismKeyBorad(usage='select_hyp')
            )

# 编辑催眠术
@dp.message_handler(commands=['edithypnotism', ])
async def set_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            await message.reply(
                '从《魔导绪论》中选择要编辑的咒语:', 
                reply_markup=user.getHypnotismKeyBorad(usage='edit_hyp')
            )
            user.stateTrans('allGood', 'editHyp')

# 删除催眠术
@dp.message_handler(commands=['deletehypnotism', ])
async def commands(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            await message.reply(
                '从《魔导绪论》中删除无用的咒语吧，注意这是无法撤销的哦:', 
                reply_markup=user.getHypnotismKeyBorad(usage='delete_hyp')
            )
            user.stateTrans('allGood', 'delHyp')

# 创建新催眠术
@dp.message_handler(commands=['newhypnotism', ])
async def set_hypnotism(message: types.Message):
    if message.chat.type == 'private':
        if await isDebugingNdeploying(message): return
        await initUser(message)
        user = users[message.chat.id]
        if user.state == 'allGood':
            user.currentReplyMsg = await message.answer(
                NEW_HYPNOTISM, parse_mode='MarkdownV2', 
                reply_markup=user.getCancelBorad()
            )
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


# ----------------------------------------------------------------------------------------
async def dialogue(user:User, message:types.Message, text:str):
    assert user.state == 'allGood'
    try:
        # 清除上一句回复的重新生成按钮
        if user.currentReplyMsg is not None:
            try:
                await user.currentReplyMsg.edit_reply_markup(None)
            except aiogram.exceptions.MessageNotModified:
                pass
            
        # openai请求
        user.currentReplyMsg = await message.answer(f'{user.character} 正在思考...')
        response = user.getReply(text, True)

        # 流式打印回复
        reply, replys = '', []
        for chunk in response:
            repLen = len(reply)
            content = chunk.choices[0].delta.content

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

            if content is not None:
                reply += content

        # 完成最后一段回复，增加重新生成按钮
        replys.append(reply)
        await editInMarkdown(user, reply)
        await user.currentReplyMsg.edit_reply_markup(user.getReGenKeyBorad())
    
        # 还原完整回复
        full_reply = ''.join(replys)

        # 更新上下文
        if user.state != 'creatingImg':
            user.history['assistant'].insert(0, full_reply)

    except UnicodeEncodeError as e:
        reply = f'出错了...\n\n{str(e)}\n\n这很可能是因为您输入了带中文的API Key，请点击左下角菜单重新设置'        
        await editInMarkdown(user, reply)
        print(f'[get reply error]: user{message.chat.first_name}', e)
    except openai.AuthenticationError as e:
        reply = '出错了\.\.\.\n\n'+str('您输入的 openai API key 有误，可能是*API已经被销毁*或请*API格式不对*。注意 API 带 sk\- 前缀，形如\n\n `sk\-bJWSrupJ4VPxiYnw4s0UT3BlbkFJh8BQxx4yWSMFfjPnAz5I`\n\n请在 [Openai官网](https://platform\.openai\.com/account/api\-keys) 查看您的 API Key')        
        await message.answer(reply, parse_mode='MarkdownV2')
    except Exception as e:
        reply = '出错了...\n\n'+str(e)        
        await editInMarkdown(user, reply)
        print(f'[get reply error]: user{message.chat.first_name}', e)      

# 获取voice消息
@dp.message_handler(content_types=types.ContentType.VOICE)
async def voice(message: types.Message):
    if message.chat.type == 'private':   
        if await isDebugingNdeploying(message): return
        await initUser(message, typing=True)
        user = users[message.chat.id]

        # 仅在聊天时接受语音消息
        if user.state != 'allGood':
            return

        # 获取用户发送的语音消息
        user.currentReplyMsg = await message.reply(f'{user.character} 正在识别语音内容...')
        voice = message.voice
        voice_path = f'./audio/{user.id}_in{voice.file_id}.mp3'
        await bot.download_file_by_id(voice.file_id, destination=voice_path)

        # 转文本
        text = user.voice2text(voice_path)
        await editInMarkdown(user, f'识别为：{text}')
        
        # 进行聊天
        await dialogue(user, message, text)     

# 获取chat消息
@dp.message_handler()
async def chat(message: types.Message):
    if message.chat.type == 'private':   
        if await isDebugingNdeploying(message): return
        await initUser(message, typing=True)
        
        # 配合完成 User 配置 
        if message.chat.id in users:
            user = users[message.chat.id]
            text = message.text

            # 设置API key
            if user.state == 'settingChatKey':       
                user = users[message.chat.id]
                user.setOpenAIKey(text)
                updateUserKey(cursor, connection, user.id, user.key)
                await message.reply(f'Openai API Key设置为:\n\n{user.key}\n\n现在就开始聊天吧!')
                user.stateTrans('settingChatKey', 'setApiKeyDone')
                return

            # 设置 Img API key
            elif user.state == 'settingImgKey':       
                user = users[message.chat.id]
                user.setSDKey(text)
                updateUserImgKey(cursor, connection, user.id, user.imgKey)
                await message.reply(f'Stable Diffusion API Key设置为:\n\n{user.imgKey}\n\n请点击左下菜单或 /howtogetimg 查看生成图像的正确方式')
                user.stateTrans('settingImgKey', 'setImgKeyDone')
                return

            # 设置上下文长度
            elif user.state == 'settingContextLen': 
                lenContext = 5
                try:
                    lenContext = int(text)
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
                if user.currentEdittingChar is None:
                    # 没有点击选项而是直接发消息，认为用户放弃操作
                    user.stateTrans('edittingHyp', 'editHypCancel')
                else:
                    user.hypnotism[user.currentEdittingChar] = text
                    updateUserPrompts(cursor, connection, user.id, user.hypnotism)
                    await message.reply(f'咒语【{user.currentEdittingChar}】编辑完成！想要使用这条咒语的话，需要先在《魔导绪论》中点选催眠哦')
                    user.stateTrans('edittingHyp', 'editHypDone')              
                    return    
            
            # 删除咒语
            elif user.state == 'deletingHyp':
                # 没有点击选项而是直接发消息，认为用户放弃操作
                user.stateTrans('deletingHyp', 'delHypCancel')

        # 进行聊天
        user = users[message.chat.id]
        if user.state == 'allGood':
            await dialogue(user, message, message.text)      

# -----------------------------------------------------------------------------
# 取消当前操作
@dp.callback_query_handler(lambda call: call.data == 'cancel')
async def cancel(call: types.CallbackQuery, ):
    user = users[call.message.chat.id]
    if user.state != 'allGood':
        await call.message.answer('已取消')

    if user.state == 'settingChatKey':       
        user.stateTrans('settingChatKey', 'setApiKeyCancel')
    elif user.state == 'settingImgKey':                       
        user.stateTrans('settingImgKey', 'setImgKeyCancel')
    elif user.state == 'creatingNewHyp':
        user.stateTrans('creatingNewHyp', 'newHypCancel')
    elif user.state == 'edittingHyp':
        user.stateTrans('edittingHyp', 'editHypCancel')
    elif user.state == 'deletingHyp':
        user.stateTrans('deletingHyp', 'delHypCancel')
    else:
        print(f"[check]: try to cancel at state '{user.state}'")
    
# 选用催眠术
@dp.callback_query_handler(lambda call: call.data.startswith('set_model'))
async def selectModel(call: types.CallbackQuery, ):
    user = users[call.message.chat.id]
    user.model = call.data[len('set_model'):]
    user.clearHistory()
    await call.message.answer(f'模型已设置为【{user.model}】')

# 选用催眠术
@dp.callback_query_handler(lambda call: call.data.startswith('select_hyp'))
async def selectHypnotism(call: types.CallbackQuery, ):
    user = users[call.message.chat.id]
    user.character = call.data[len('select_hyp'):]
    if user.character != 'GPT':
        user.system = user.hypnotism[user.character]
        await call.message.answer(f'已经使用如下咒语将 GPT 催眠为【{user.character}】，可以随意聊天，催眠术不会被遗忘\n'+'-'*35+'\n\n'+user.system+'\n\n'+'-'*35+'\n'+f'当前模型选择为【{user.model}】，可在菜单切换')
    else:
        await call.message.answer(f'不使用催眠咒语直接和 GPT 对话，当前模型选择为【{user.model}】，可在菜单切换 GPT3.5 和 GPT4.0')
    user.clearHistory()

# 删除催眠术
@dp.callback_query_handler(lambda call: call.data.startswith('delete_hyp'))
async def deleteHypnotism(call: types.CallbackQuery, ):
    character = call.data[len('delete_hyp'):]
    user = users[call.message.chat.id]
    hypDeleted = user.hypnotism[character]
    user.hypnotism.pop(character)
    updateUserPrompts(cursor, connection, user.id, user.hypnotism)
    user.clearHistory()
    await call.message.answer(f'已将咒语【{character}】删除，原文为如下\n'+'-'*35+'\n\n'+hypDeleted)
    user.stateTrans('deletingHyp', 'delHypDone')

# 编辑催眠术
@dp.callback_query_handler(lambda call: call.data.startswith('edit_hyp'))
async def editHypnotism(call: types.CallbackQuery, ):
    user = users[call.message.chat.id]
    character = call.data[len('edit_hyp'):]
    hypEditting = user.hypnotism[character]
    user.currentEdittingChar = character
    await call.message.answer(f'请直接输入咒语【{character}】的新文本，当前咒语文本如下\n'+'-'*35+'\n\n'+hypEditting)

# 生成语音回复
@dp.callback_query_handler(lambda call: call.data.startswith('audio'))
async def gen_audio(call: types.CallbackQuery, ):
    user = users[call.message.chat.id]
    message = call.message

    notice = await message.answer(f'{user.character} 正在讲话...')
    voice_path = user.text2voice(text=message.text, type=call.data)
    try:
        with open(voice_path, 'rb') as voice:
            await bot.send_voice(user.id, voice)
    except Exception as e:
        print(f'[Check]: Gen Audio failed as {e}')
    await notice.delete()

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
        content = chunk.choices[0].delta.content

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
        if content is not None:
            reply += content

    # 打印最后一段回复，增加重新生成按钮
    replys.append(reply)
    await editInMarkdown(user, reply)
    await user.currentReplyMsg.edit_reply_markup(user.getReGenKeyBorad())

    # 还原完整回复
    full_reply = ''.join(replys)

    # 更新上下文
    user.history['assistant'].insert(0, full_reply)

# -----------------------------------------------------------------------------
async def start():
    await bot.set_my_commands([
        BotCommand('sethypnotism','魔导绪论'),
        BotCommand('showhypnotism','查看当前咒语'),
        BotCommand('newhypnotism','创建新咒语'),
        BotCommand('edithypnotism','编辑咒语'),
        BotCommand('deletehypnotism','删除咒语'),
        BotCommand('setmodel','选择模型'),
        BotCommand('setcontextlen','设置上下文长度'),
        BotCommand('setapikey','设置OpenAI Key'),
        BotCommand('setimgkey','设置Stable diffusion Key'),
        BotCommand('howtogetimg','生成图像示范'),
        BotCommand('about','使用指南'),
        BotCommand('resetall','遇到严重错误时点此重置机器人')
    ])

def botActivate():
    print('bot启动中; pid = {}'.format(os.getpid()))

    getDatabaseReady(cursor, connection)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())
    loop.run_until_complete(executor.start_polling(dp))

def connectionGuard(process):
    ''' 主进程守护线程在此检查bot进程是否死亡，并自动重启 '''
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
