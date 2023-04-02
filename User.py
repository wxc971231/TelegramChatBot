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
        self.summaryCountDown = 5
        self.history = {'user':[], 'assistant':[]}

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
        self.summaryCountDown = self.contextMaxLen

    def setContextLen(self, contextMaxLen):
        self.contextMaxLen = contextMaxLen
        self.summaryCountDown = contextMaxLen

    def createMessage(self):
        users = self.history['user']
        assistants = self.history['assistant']

        users = users[:self.contextMaxLen] if len(users) > self.contextMaxLen else users
        assistants = assistants[:self.contextMaxLen-1] if len(assistants) > self.contextMaxLen-1 else assistants
        
        message = [{"role": "system", "content": self.system},] if self.system != '' else []
        for i in range(min(self.contextMaxLen, len(assistants)),0,-1):
            message.append({"role": "user", "content": users[i]})
            message.append({"role": "assistant", "content": assistants[i-1]})
        message.append({"role": "user", "content": users[0]})

        return message
    
    def getReply(self, text):
        if self.state != 'creatingImg':
            if self.system != self.hypnotism['GPT3.5']:
                text += '，扮演指定角色回答，且不要说你在扮演。'        
            text += '你此次回复的最后，必须以“summary=”开头总结咱们之前聊的内容, 实现减少token的同时，保证对话的质量' if self.summaryCountDown == 1 else '此次回复不要总结对话'
        else:
            text += '. You must write prompt in English directly, DO NOT explain or translate, omit any introductory text. Your answer must mimics the example format, i.e. a complete description sentence followed by a number of independent style words'

        if self.state != 'creatingImg':
            self.history['user'].insert(0, text)
            messages = self.createMessage()
        else:
            messages = [{"role": "user", "content": text},]

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            api_key = self.key,
            messages=messages
        )

        reply = completion.choices[0].message.content
        tokenCnt = completion._previous['usage']['total_tokens']
        #print(tokenCnt)
        if self.state != 'creatingImg':
            self.history['assistant'].insert(0, reply)

        # 自动总结，这样能多记住一点临时对话信息
        #print(self.summaryCountDown)
        if self.state != 'creatingImg':
            if self.summaryCountDown == 1:
                self.summaryCountDown = self.contextMaxLen
            summaryPos1 = reply.find('summary=')
            summaryPos2 = reply.find('Summary=')
            if not summaryPos1 == summaryPos2 == -1:
                summaryPos = summaryPos1 if summaryPos1 != -1 else summaryPos2
                print(reply[summaryPos:])
                reply = reply[:summaryPos]
        
        return reply

    def getHypnotismKeyBorad(self, usage):
        inlineKeyboard = InlineKeyboardMarkup()
        if usage == 'delete_hyp':
            inlineButton = InlineKeyboardButton(text='【取消修改】', callback_data=usage+'【取消修改】')      # 这里的callback_data是点击是调用的函数名
            inlineKeyboard.add(inlineButton)

        self.hypnotism = getUserPrompts(self.cursor, self.connection, self.id)
        for character in self.hypnotism.keys():
            inlineButton = InlineKeyboardButton(text=character, callback_data=usage+character)      # 这里的callback_data是点击是调用的函数名
            inlineKeyboard.add(inlineButton)
        
        return inlineKeyboard

    
