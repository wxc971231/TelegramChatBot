from openai import OpenAI
from transitions import Machine
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Data import initUser, getUserPrompts
from datetime import datetime
from pydub import AudioSegment
import requests
import io
import math
from Utils import transitions, states
from MagicBook import *

USER_STATUS_INIT = 0
USER_STATUS_SETTINGKEY = 1
USER_STATUS_SETTINGCONTEXT = 2
USER_STATUS_NEWHYP = 3
USER_STATUS_ALLGOOD = 4

MODEL_GPT35 = 'gpt-3.5-turbo'
MODEL_GPT40 = 'gpt-4'

class User():
    def __init__(self, name, id, cursor, connection, key=None) -> None:
        self.name = name
        self.id = id
        self.key = key   
        self.imgKey = None
        self.voiceToken = None
        self.cursor = cursor
        self.connection = connection

        self.client = None if key is None else OpenAI(api_key=key)
        self.hypnotism = initUser(cursor, connection, id)
        self.model = MODEL_GPT35
        self.character = 'GPT'
        self.system = ''
        self.contextMaxLen = 5
        self.immersion = False
        self.history = {'user':[], 'assistant':[]}
        self.voice_type = 'OpenAI'
        self.voice_sex = 'female'
        self.voice = 'Nova'

        self.currentVoiceMsg = None
        self.currentReplyMsg = None
        self.currentEdittingChar = None

        self.log = f'./ChatLog/{self.name}_{self.id}.txt'
        self.stateMachine = Machine(model=self, states=states, transitions=transitions, initial='init')

    def stateTrans(self, source:str, trigger:str):
        if self.state == source:
            getattr(self, trigger)()

    def setOpenAIKey(self, key):
        assert key is not None
        self.key = key
        self.client = OpenAI(api_key=key)
    
    def setSDKey(self, key):
        self.imgKey = key

    def setVoiceKey(self, token):
        self.voiceToken = token

    def clearHistory(self):
        self.history = {'user':[], 'assistant':[]}

    def setContextLen(self, contextMaxLen):
        self.contextMaxLen = contextMaxLen

    def createMessage(self, text=''):
        if self.state != 'creatingImg':
            users = self.history['user']
            assistants = self.history['assistant']

            # 如果 text 为空，是在重新生成之前的回答
            if text != '':
                #if self.character != 'GPT':
                #    text += '，扮演指定角色回答。'  # 当前用户发言预处理
                users.insert(0, text)

            # 组合上下文
            users = users[:self.contextMaxLen]
            assistants = assistants[:self.contextMaxLen-1]
            message = [{"role": "system", "content": self.system},] if self.character != 'GPT' else []
            for i in range(min(self.contextMaxLen, len(assistants)),0,-1):
                message.append({"role": "user", "content": users[i]})
                message.append({"role": "assistant", "content": assistants[i-1]})
            message.append({"role": "user", "content": users[0]})
        else:
            text += '. You must write prompt in English directly, DO NOT explain or translate, omit any introductory text. Your answer must mimics the example format, i.e. a complete description sentence followed by a number of independent style words'
            message = [{"role": "user", "content": text},]

        return message
    
    def voice2text(self, voice_path:str):
        with open(voice_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="text"
            )
        return transcript

    def text2voice(self, text:str):
        return self.text2voice_test(voice=self.voice, text=text)

    def text2voice_test(self, voice:str, text:str):
        audio_path = f'./Audio/{self.id}_{datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]}.ogg'
        if voice in VOICE_OPENAI_MALE or voice in VOICE_OPENAI_FEMALE:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice.lower(),
                input=text,
                response_format='opus'
            )
            response.stream_to_file(audio_path)
        else:
            token = self.voiceToken
            response = requests.post('https://tirs.ai-lab.top/api/status', json={'token':token})
            data = response.json()
            if not data['is_ok']:
                raise ValueError('Voice Token 已失效，请重新生成')

            url = "https://tirs.ai-lab.top/api/ex/vits"
            payload = {
                "lang": "zh",
                "appid": "9tuof1o8y7ni8h3e",
                "text": text,
                "speaker": voice,
                "sdp_ratio": 0.2,
                "noise": 0.6,
                "noisew": 0.8,
                "length": 1,
                "token": token
            }

            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                audio_url = data["audio"]
                if data["status"] == 1:    
                    # 生成成功，下载音频文件
                    audio_response = requests.get(audio_url)
                    if audio_response.status_code == 200:    
                        audio_content = io.BytesIO(audio_response.content)
                        # wav转ogg
                        sound = AudioSegment.from_wav(audio_content)
                        sound.export(audio_path, format="ogg")
                    else:
                        raise ValueError("音频文件下载失败")
                else:
                    raise ValueError(data["message"])
            else:
                raise ValueError(f"API请求失败，状态码:{response.status_code}")
        return audio_path

    def getReply(self, text, useStreamMode=False):
        messages = self.createMessage(text)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=useStreamMode
        )
        if useStreamMode:
            return response
        else:
            return response.choices[0].message.content

    def getHypnotismKeyBorad(self, usage):
        inlineKeyboard = InlineKeyboardMarkup()
        if usage in ['delete_hyp', 'edit_hyp']:
            inlineButton = InlineKeyboardButton(text='【取消修改】', callback_data='cancel')     
            inlineKeyboard.add(inlineButton)

        self.hypnotism = getUserPrompts(self.cursor, self.connection, self.id)
        for character in self.hypnotism.keys():
            if character.startswith('GPT'):
                inlineButton = InlineKeyboardButton(text='GPT', callback_data=usage+'GPT')
            else:
                inlineButton = InlineKeyboardButton(text=character, callback_data=usage+character)

            inlineKeyboard.add(inlineButton)

        return inlineKeyboard

    def getCancelBorad(self):
        inlineKeyboard = InlineKeyboardMarkup()
        inlineButton = InlineKeyboardButton(text='【取消并继续聊天】', callback_data='cancel')     
        inlineKeyboard.add(inlineButton)
        return inlineKeyboard

    def getReGenKeyBorad(self):
        inlineKeyboard = InlineKeyboardMarkup(row_width=2)
        inlineButton_audio_gen = InlineKeyboardButton(text=f'【用{self.voice}的声音读】', callback_data='audio_gen')
        inlineButton_audio_select = InlineKeyboardButton(text='【选择声音】', callback_data='audio_select')
        inlineKeyboard.row(inlineButton_audio_gen, inlineButton_audio_select)
        inlineButton_immersion = InlineKeyboardButton(text='【沉浸模式】', callback_data='immersion')
        inlineButton_regen = InlineKeyboardButton(text='【重新回答】', callback_data='regenerate')
        inlineKeyboard.row(inlineButton_immersion, inlineButton_regen)
        return inlineKeyboard

    def getModelKeyBorad(self):
        inlineKeyboard = InlineKeyboardMarkup()
        inlineButton35 = InlineKeyboardButton(text=MODEL_GPT35, callback_data='set_model'+MODEL_GPT35)     
        inlineButton40 = InlineKeyboardButton(text=MODEL_GPT40, callback_data='set_model'+MODEL_GPT40)     
        inlineKeyboard.add(inlineButton35, inlineButton40)
        return inlineKeyboard

    def getImmersionBorad(self):
        inlineKeyboard = InlineKeyboardMarkup()
        inlineButton_immersion = InlineKeyboardButton(text='【退出沉浸模式】', callback_data='immersion')     
        inlineButton_regen = InlineKeyboardButton(text='【重新回答】', callback_data='regenerate')     
        inlineKeyboard.add(inlineButton_immersion)
        inlineKeyboard.add(inlineButton_regen)
        return inlineKeyboard
    
    def getVoiceTokenBorad(self):
        inlineKeyboard = InlineKeyboardMarkup(row_width=1)
        inlineButton_back = InlineKeyboardButton(text='【返回】', callback_data='audio_back_to_select_type')
        inlineKeyboard.add(inlineButton_back)
        return inlineKeyboard

    def getVoiceTypeBorad(self):
        inlineKeyboard = InlineKeyboardMarkup(row_width=1)
        inlineButton_audio_openai = InlineKeyboardButton(text=f'【OpenAI】', callback_data='audio_OpenAI')
        inlineButton_audio_genshin = InlineKeyboardButton(text='【Genshin】', callback_data='audio_Genshin')
        inlineKeyboard.row(inlineButton_audio_openai, inlineButton_audio_genshin)
        inlineButton_back = InlineKeyboardButton(text='【返回】', callback_data='audio_back')
        inlineKeyboard.add(inlineButton_back)
        return inlineKeyboard

    def getVoiceSexBorad(self):
        inlineKeyboard = InlineKeyboardMarkup(row_width=1)
        inlineButton_audio_male = InlineKeyboardButton(text=f'【男声】', callback_data='audio_male')
        inlineButton_audio_female = InlineKeyboardButton(text='【女声】', callback_data='audio_female')
        inlineKeyboard.row(inlineButton_audio_male, inlineButton_audio_female)
        inlineButton_back = InlineKeyboardButton(text='【返回】', callback_data='audio_back_to_select_type')
        inlineKeyboard.add(inlineButton_back)
        return inlineKeyboard
    
    def getVoiceBorad(self):
        voices = VOICES[self.voice_type][self.voice_sex]
        inlineKeyboard = InlineKeyboardMarkup(row_width=math.floor(len(voices)/3))
        for i in range(0, len(voices), 3):
            row = []
            for voice in voices[i:i+3]:
                inlineButton = InlineKeyboardButton(text=voice, callback_data=f'audio_{voice}')
                row.append(inlineButton)
            inlineKeyboard.row(*row)
        inlineButton_back = InlineKeyboardButton(text='【返回】', callback_data='audio_back_to_select_sex')
        inlineKeyboard.add(inlineButton_back)
        return inlineKeyboard

    def getDebugBorad(self):
        inlineKeyboard = InlineKeyboardMarkup(row_width=1)
        inlineButton_debug_audio = InlineKeyboardButton(text=f'【声音测试】', callback_data='debug_audio')
        inlineKeyboard.add(inlineButton_debug_audio)
        return inlineKeyboard