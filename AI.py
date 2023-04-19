import re
import json
import asyncio
import threading
import tiktoken
from parser import url_article_parser, get_parser_params
from config import API, NICK, COOKIES
from telegram import ChatAction
from revChatGPT.V3 import Chatbot as GPT
from EdgeGPT import Chatbot as BingAI, ConversationStyle
from aiogram import types

class AIBot:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.LastMessage_id = ''
        self.mess = ''
        self.BingActive = False
        self.GPTActive = False
        self.max_tokens = 4000
        self.ConversationStyle = ConversationStyle.balanced
        if COOKIES:
            self.Bingbot = BingAI(cookies=json.loads(COOKIES))
            self.BingActive = True
        if API:
            self.ChatGPTbot = GPT(api_key=f"{API}")
            self.GPTActive = False
        self.botNick = NICK if NICK else None #.lower()
        self.botNicKLength = len(self.botNick) if self.botNick else 0
        # print("nick:", self.botNick)

    async def typing(self, update, context):
        context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING, timeout=60)
        
    async def getBing(self, message, update, context):
        await self.typing(update, context)
        result = ''
        prompt = ""
        try:
            result = await self.Bingbot.ask(prompt=prompt + message, conversation_style=self.ConversationStyle)
            numMessages = result["item"]["throttling"]["numUserMessagesInConversation"]
            maxNumMessages = result["item"]["throttling"]["maxNumUserMessagesInConversation"]
            print(numMessages, "/", maxNumMessages, end="\n")
            result = result["item"]["messages"][1]["text"]
            if numMessages == maxNumMessages:
                await self.Bingbot.reset()
        except Exception as e:
            print('\033[31m')
            print("response_msg", result)
            print("error", e)
            print('\033[0m')
            result = "Bing: Something went wrong"
        result = re.sub(r"\[\^\d+\^\]", '', result)
        # print(" BingAI", result)
        if self.LastMessage_id == '':
            message = context.bot.send_message(
                chat_id=update.message.chat_id,
                text="▎Bing\n" + result,
                # parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=update.message.message_id,
            )
            self.mess = "▎Bing\n" + result
            if COOKIES and API and self.GPTActive:
                self.LastMessage_id = message.message_id
            # print("LastMessage_id", self.LastMessage_id)
        else:
            context.bot.edit_message_text(chat_id=update.message.chat_id, message_id=self.LastMessage_id, text=self.mess + "\n\n▎Bing\n" + result)
            self.LastMessage_id = ''
            self.mess = ''
    
    async def resetBing(self):
        await self.Bingbot.reset()
    
    def getChatGPT(self, message, update, context):
        result = ''
        try:
            for data in self.ChatGPTbot.ask(message):
                result += data
        except Exception as e:
            print('\033[31m')
            print("response_msg", result)
            print("error", e)
            print('\033[0m')
            result = "ChatGPT: Something went wrong"
        # print("ChatGPT", result)
        if self.LastMessage_id == '':
            message = context.bot.send_message(
                chat_id=update.message.chat_id,
                text="▎ChatGPT3.5\n" + result,
                reply_to_message_id=update.message.message_id,
            )
            if COOKIES and API and self.BingActive:
                self.LastMessage_id = message.message_id
            self.mess = "▎ChatGPT3.5\n" + result
            # print("LastMessage_id", self.LastMessage_id)
        else:
            context.bot.edit_message_text(chat_id=update.message.chat_id, message_id=self.LastMessage_id, text=self.mess + "\n\n▎ChatGPT3.5\n" + result)
            self.LastMessage_id = ''
            self.mess = ''

    def getResult(self, update, context):
        article_text = []
        url_yes = False
        parser_option = 1
        orig_url = False
        reply_to_text: str=''
        chat_content: str=''
        if update.message.text:
          msg = update.message
        elif update.edited_message.text:
          msg = update.edited_message
        else:
          msg = []
        # print("\033[32m", update.effective_user.username, update.effective_user.id, update.message.text, "\033[0m")
        if (not update.effective_chat.type and update.effective_chat.type != types.ChatType.GROUP) or NICK is None:
          chat_content = msg.text
        elif msg:
          if self.botNick in msg.text:
            chat_content = msg.text.replace(self.botNick, '').strip()
          else:
            return       
        else:
          return
          
        if msg.entities is not None:
          for entity in msg.entities:
            if entity.type == "url":
              url = msg.text[entity.offset: entity.offset + entity.length]
              if url.startswith('http'):
                params = get_parser_params(msg.text)
                parser_option = params['parser_option']
                orig_url = params['orig_url']
                article_text = url_article_parser(url=url, parser_option=parser_option, orig_url=orig_url)
                chat_content = chat_content.replace(f'parser_option{parser_option}', '').strip()
                chat_content = chat_content.replace('orig_url', '').strip()
                if article_text != '':
                  chat_content = chat_content.replace(url, '').strip()
                  chat_content = chat_content + "\n" + article_text

        if msg.reply_to_message:
          if msg.reply_to_message.entities is not None:
            for entity in msg.reply_to_message.entities:
              if entity.type == "url":
                url = msg.reply_to_message.text[entity.offset: entity.offset + entity.length]
                if url.startswith('http'):
                  params = get_parser_params(msg.text)
                  parser_option = params['parser_option']
                  orig_url = params['orig_url']
                  article_text = url_article_parser(url=url, parser_option=parser_option, orig_url=orig_url)
                  chat_content = chat_content.replace(f'parser_option{parser_option}', '').strip()
                  chat_content = chat_content.replace('orig_url', '').strip()
                  if article_text != '':
                    url_yes = True
                    chat_content = chat_content + "\n" + article_text
                    break

          if not url_yes:           
            if msg.reply_to_message.text:
              reply_to_text = msg.reply_to_message.text
              if self.botNick in reply_to_text:
                reply_to_text = reply_to_text.replace(self.botNick, '')
              if reply_to_text:
                chat_content = chat_content + "\n" + reply_to_text
            elif msg.reply_to_message.caption:
              chat_content = chat_content + "\n" + msg.reply_to_message.caption

        chat_content = chat_content.replace('▎ChatGPT3.5\n', '').strip()
        chat_content = chat_content.replace('▎Bing\n', '').strip()
        chat_content = re.sub(r'[^\w\s.,!?;:()\[\]{}<>\'\"@#$%^&*=+-/\\]', '', chat_content)
        chat_content = chat_content.strip()
        prompt_len = get_prompt_len(prompt=[{"role": "user", "content": chat_content}])
        if prompt_len > self.max_tokens:
          context.bot.send_message(
              chat_id = update.message.chat_id,
              text = f'Длина запроса {prompt_len} токенов > максимальной длины разговора {self.max_tokens}',
              parse = "HTML",
          )          
          return

        if COOKIES and chat_content and self.BingActive:
            _thread = threading.Thread(target=self.loop.run_until_complete, args=(self.getBing(chat_content, update, context),))
            _thread.start()
        if API and chat_content and self.GPTActive:
            self.getChatGPT(chat_content, update, context)
    
    def reset_chat(self, update, context):
        if API:
            self.ChatGPTbot.reset()
            self.GPTActive = False
        if COOKIES:
            self.BingActive = True
            self.loop.run_until_complete(self.resetBing())
            self.Conversation = ConversationStyle.balanced
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Reset successfully",
        )
        self.LastMessage_id = ''
        self.mess = ''
      
    def gpt_off(self, update, context):
        self.GPTActive = False
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="ChatGPT Deactivated",
        )
      
    def gpt_on(self, update, context):
        self.GPTActive = True
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="ChatGPT Activated",
        )      
      
    def bing_off(self, update, context):
        self.BingActive = False
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Bing Dectivated",
        )
      
    def bing_on(self, update, context):
        self.BingActive = True
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Bing Activated",
        )     
      
    def bing_balanced(self, update, context):
        self.Conversation = ConversationStyle.balanced
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Bing Conversation Stype is now Balanced",
        )    

    def bing_precise(self, update, context):
        self.Conversation = ConversationStyle.precise
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Bing Conversation Stype is now Precise",
        )   

    def bing_creative(self, update, context):
        self.Conversation = ConversationStyle.creative
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Bing Conversation Stype is now Creative",
        )
      
def get_prompt_len(prompt: dict) -> int:
  tiktoken.model.MODEL_TO_ENCODING["gpt-4"] = "cl100k_base"
  encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
  num_tokens = 0
  # every message follows <im_start>{role/name}\n{content}<im_end>\n
  num_tokens += 5
  for msg in prompt:
    for key, value in msg.items():
      num_tokens += len(encoding.encode(value))
      if key == "name":  # if there's a name, the role is omitted
        num_tokens += 5  # role is always required and always 1 token
  return num_tokens