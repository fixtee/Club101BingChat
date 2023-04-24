import logging
from AI import AIBot
from config import MODE
from telegram import BotCommand
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
ai_bot = AIBot()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# In all other places characters
# _ * [ ] ( ) ~ ` > # + - = | { } . ! 
# must be escaped with the preceding character '\'.
def start(update, context): # When the user enters/start, the text is returned
    user = update.effective_user
    update.message.reply_html(
        rf"Hi {user.mention_html()} I will provide assistance using both ChatGPT and BingChat.",
    )

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    print('Context error appeared', context.error)
    if not context.error:
      context.bot.send_message(chat_id=update.effective_chat.id, text="Something went wrong\! Please try again\.\n\n", parse_mode='MarkdownV2')

def unknown(update, context): # When the user enters an unknown command, text is returned
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

def setup(token):
    updater = Updater(token, use_context=True, request_kwargs={
        'proxy_url': 'http://127.0.0.1:6152' if MODE == "dev" else None
    })

    updater.bot.set_my_commands([
        BotCommand('start', 'Start the bot'),
        BotCommand('reset', 'Reset the bot'),
        BotCommand('gpt_off', 'Deactivate ChatGPT'),
        BotCommand('gpt_on', 'Activate ChatGPT'),
        BotCommand('bing_off', 'Deactivate BingChat'),
        BotCommand('bing_on', 'Activate BingChat'),      
        BotCommand('bing_balanced', 'Set Bing to Balanced style'),
        BotCommand('bing_precise', 'Set Bing to Precise style'),
        BotCommand('bing_creative', 'Set Bing to Creative style'),       
    ])

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("reset", ai_bot.reset_chat))
    dispatcher.add_handler(CommandHandler("gpt_off", ai_bot.gpt_off))
    dispatcher.add_handler(CommandHandler("gpt_on", ai_bot.gpt_on))
    dispatcher.add_handler(CommandHandler("bing_off", ai_bot.bing_off))
    dispatcher.add_handler(CommandHandler("bing_on", ai_bot.bing_on))
    dispatcher.add_handler(CommandHandler("bing_balanced", ai_bot.bing_balanced))
    dispatcher.add_handler(CommandHandler("bing_precise", ai_bot.bing_precise))
    dispatcher.add_handler(CommandHandler("bing_creative", ai_bot.bing_creative))  
    dispatcher.add_handler(MessageHandler(Filters.text, ai_bot.getResult))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    dispatcher.add_error_handler(error)

    return updater, dispatcher