import openai
import os
from MagicBook import DEFAULT_HYPNOTISM
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv 

class User():
    def __init__(self, key) -> None:
        self.hypnotism = DEFAULT_HYPNOTISM.copy()
        self.character = 'GPT3.5'
        self.system = self.hypnotism[self.character]
        self.contextMaxLen = 5
        self.history = {'user':[], 'assistant':[]}
        self.key = key
    
    def clearHistory(self):
        self.history = {'user':[], 'assistant':[]}

    def setContextLen(self, contextMaxLen):
        self.contextMaxLen = contextMaxLen

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
        if self.system != self.hypnotism['GPT3.5']:
            text += '，扮演指定角色回答，且不要说你在扮演'

        self.history['user'].insert(0, text)
        messages = self.createMessage()

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            api_key = self.key,
            messages=messages
        )

        reply = completion.choices[0].message.content
        self.history['assistant'].insert(0, reply)
        return reply

    def getHypnotismKeyBorad(self):
        inlineKeyboard = InlineKeyboardMarkup()
        for sys in self.hypnotism.keys():
            inlineButton = InlineKeyboardButton(text=sys, callback_data=sys)      # 这里的callback_data是点击是调用的函数名
            inlineKeyboard.add(inlineButton)
        return inlineKeyboard
