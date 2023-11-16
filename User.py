from openai import OpenAI
from transitions import Machine
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Data import initUser, getUserPrompts, updateUserPrompts
from Utils import transitions, states
from datetime import datetime

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
        self.cursor = cursor
        self.connection = connection

        self.client = None if key is None else OpenAI(api_key=key)
        self.hypnotism = initUser(cursor, connection, id)
        self.model = MODEL_GPT35
        self.character = 'GPT'
        self.system = ''
        self.contextMaxLen = 5
        self.history = {'user':[], 'assistant':[]}

        self.currentReplyMsg = None
        self.currentEdittingChar = None

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
                if self.character != 'GPT':
                    text += '，扮演指定角色回答。'  # 当前用户发言预处理
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

    def text2voice(self, text:str, type:str):
        audio_path = f'./audio/{self.id}_{datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]}.ogg'
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="nova" if type.endswith('female') else 'alloy',
            input=text,
            response_format='opus'
        )
        response.stream_to_file(audio_path)
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
        inlineButton = InlineKeyboardButton(text='【取消】', callback_data='cancel')     
        inlineKeyboard.add(inlineButton)
        return inlineKeyboard

    def getReGenKeyBorad(self):
        inlineKeyboard = InlineKeyboardMarkup(row_width=2)
        inlineButton_audio_female = InlineKeyboardButton(text='【生成音频 (女)】', callback_data='audio_female')
        inlineButton_audio_male = InlineKeyboardButton(text='【生成音频 (男)】', callback_data='audio_male')
        inlineKeyboard.row(inlineButton_audio_female, inlineButton_audio_male)
        inlineButton_regen = InlineKeyboardButton(text='【重新回答】', callback_data='regenerate')
        inlineKeyboard.add(inlineButton_regen)
        return inlineKeyboard


    def getModelKeyBorad(self):
        inlineKeyboard = InlineKeyboardMarkup()
        inlineButton35 = InlineKeyboardButton(text=MODEL_GPT35, callback_data='set_model'+MODEL_GPT35)     
        inlineButton40 = InlineKeyboardButton(text=MODEL_GPT40, callback_data='set_model'+MODEL_GPT40)     
        inlineKeyboard.add(inlineButton35, inlineButton40)
        return inlineKeyboard