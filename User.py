import openai
from transitions import Machine
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Data import initUser, getUserPrompts, updateUserPrompts
from Utils import transitions, states

USER_STATUS_INIT = 0
USER_STATUS_SETTINGKEY = 1
USER_STATUS_SETTINGCONTEXT = 2
USER_STATUS_NEWHYP = 3
USER_STATUS_ALLGOOD = 4

class User():
    def __init__(self, name, id, cursor, connection, key=None) -> None:
        self.name = name
        self.id = id
        self.key = key   
        self.imgKey = None
        self.cursor = cursor
        self.connection = connection

        self.hypnotism = initUser(cursor, connection, id)
        self.character = 'GPT3.5'
        self.system = self.hypnotism[self.character]
        self.contextMaxLen = 5
        self.history = {'user':[], 'assistant':[]}

        self.currentReplyMsg = None
        self.currentEdittingChar = None

        self.log = f'./ChatLog/{self.name}_{self.id}.txt'
        self.stateMachine = Machine(model=self, states=states, transitions=transitions, initial='init')

    def stateTrans(self, source:str, trigger:str):
        if self.state == source:
            getattr(self, trigger)()

    def setOpenAIKey(self, key):
        self.key = key
    
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
                if self.system != self.hypnotism['GPT3.5']:
                    text += '，扮演指定角色回答，且不要说你在扮演。'  # 当前用户发言预处理
                users.insert(0, text)

            # 组合上下文
            users = users[:self.contextMaxLen]
            assistants = assistants[:self.contextMaxLen-1]
            message = [{"role": "system", "content": self.system},] if self.character != 'GPT3.5' else []
            for i in range(min(self.contextMaxLen, len(assistants)),0,-1):
                message.append({"role": "user", "content": users[i]})
                message.append({"role": "assistant", "content": assistants[i-1]})
            message.append({"role": "user", "content": users[0]})
        else:
            text += '. You must write prompt in English directly, DO NOT explain or translate, omit any introductory text. Your answer must mimics the example format, i.e. a complete description sentence followed by a number of independent style words'
            message = [{"role": "user", "content": text},]

        return message
    
    def getReply(self, text, useStreamMode=False):
        messages = self.createMessage(text)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            api_key = self.key,
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
            inlineButton = InlineKeyboardButton(text='【取消修改】', callback_data=usage+'【取消修改】')     
            inlineKeyboard.add(inlineButton)

        self.hypnotism = getUserPrompts(self.cursor, self.connection, self.id)
        for character in self.hypnotism.keys():
            inlineButton = InlineKeyboardButton(text=character, callback_data=usage+character)
            inlineKeyboard.add(inlineButton)

        return inlineKeyboard

    def getReGenKeyBorad(self):
        inlineKeyboard = InlineKeyboardMarkup()
        inlineButton = InlineKeyboardButton(text='【重新生成这句回答】', callback_data='regenerate')     
        inlineKeyboard.add(inlineButton)
        return inlineKeyboard