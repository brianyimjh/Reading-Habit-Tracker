from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters, CallbackContext
from emoji import emojize

import os
import logging
import html
import traceback
import json

# TOKEN = os.environ.get("SANDBOX_TOKEN")
TOKEN = os.environ.get("PRODUCTION_TOKEN")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

NUM_OF_DAYS, NAME_OF_BOOKS = range(2)
EDITED = 0
PINNED_MESSAGE_ID = 0
PINNED_MESSAGE = ''

logger = logging.getLogger(__name__)

def init(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    logger.info(f'{user.username} initialized the bot')

    pinned_msg = context.bot.send_message(chat_id, 'READERS', disable_notification=True)
    context.bot.edit_message_text(f'READERS\nMessage ID:{pinned_msg.message_id}',chat_id, pinned_msg.message_id)
    context.bot.pin_chat_message(chat_id, pinned_msg.message_id, disable_notification=True)

def start(update, context):
    global PINNED_MESSAGE_ID, PINNED_MESSAGE

    user = update.message.from_user
    chat_id = update.message.chat_id
    logger.info(f'{user.username} started the bot')

    current_chat_pinned_msg = context.bot.get_chat(chat_id).pinned_message
    PINNED_MESSAGE_ID = current_chat_pinned_msg.text.split('\n')[1].split(':')[1]
    PINNED_MESSAGE = current_chat_pinned_msg.text

    update.message.reply_text(f'Hello {user.first_name} {user.last_name}! Welcome to the reading bot! How many days have you been reading?\n\nSend /cancel to stop.')

    return NUM_OF_DAYS

def num_of_days(update, context):
    user = update.message.from_user
    logger.info(f'{user.username} has been reading for {update.message.text} days')

    context.user_data['num_of_days'] = update.message.text

    update.message.reply_text(f'If you have completed any book(s), please send the name(s) of the book(s) in the following format:\n\nBook1\nBook2\nBook3\nBook4\nBook5\n...\n\nSend /skip if you have not completed any books')

    return NAME_OF_BOOKS

def name_of_books(update, context):
    global PINNED_MESSAGE_ID, PINNED_MESSAGE

    user = update.message.from_user
    chat_id = update.message.chat_id
    logger.info(f'{user.username} has completed the following books:\n{update.message.text}')

    books = update.message.text.split('\n')

    text = f'\n\n{user.username} - Day ' + context.user_data['num_of_days']
    for book in books:
        text += f'\n{book} ' + emojize(':check_mark_button:')

    PINNED_MESSAGE += text

    context.bot.edit_message_text(PINNED_MESSAGE, chat_id, PINNED_MESSAGE_ID)

    update.message.reply_text('All done!!')

    return ConversationHandler.END

def skip_books(update, context):
    global PINNED_MESSAGE_ID, PINNED_MESSAGE

    user = update.message.from_user
    chat_id = update.message.chat_id
    logger.info(f'{user.username} has not completed any book')

    text = f'\n\n{user.username} - Day ' + context.user_data['num_of_days']

    PINNED_MESSAGE += text

    context.bot.edit_message_text(PINNED_MESSAGE, chat_id, PINNED_MESSAGE_ID)

    update.message.reply_text('All done!!')

    return ConversationHandler.END

def clock(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    logger.info(f'{user.username} clocked for the day')

    current_chat_pinned_msg = context.bot.get_chat(chat_id).pinned_message
    pinned_msg_id = current_chat_pinned_msg.text.split('\n')[1].split(':')[1]
    pinned_msg = current_chat_pinned_msg.text

    all_readers = {}

    readers = pinned_msg.split('\n\n')
    header = readers[0]

    for i in range(1, len(readers)):
        reader_books = []
        reader_data = readers[i].split('\n')

        reader_username = reader_data[0].split()[0]
        reader_num_of_days = int(reader_data[0].split()[-1])

        for x in range(1, len(reader_data)):
            reader_books.append(reader_data[x])

        all_readers[reader_username] = {'days': reader_num_of_days, 'books': reader_books}

    if user.username in all_readers:
        all_readers[user.username]['days'] += 1
        text = ''
        
        text += header
        for k,v in all_readers.items():
            text += f'\n\n{k} - Day ' + str(v['days'])
            for book in v['books']:
                text += f'\n{book}'

        context.bot.edit_message_text(text, chat_id, pinned_msg_id)
        logger.info(f"{user.username} is now on Day {all_readers[user.username]['days']}")
        context.bot.send_message(chat_id, f"{user.username} is now on Day {all_readers[user.username]['days']}")

    else:
        update.message.reply_text('Please send /start to add reader first')

def edit(update, context):
    global PINNED_MESSAGE_ID, PINNED_MESSAGE

    user = update.message.from_user
    chat_id = update.message.chat_id
    logger.info(f'{user.username} has edited the pinned message')

    current_chat_pinned_msg = context.bot.get_chat(chat_id).pinned_message
    PINNED_MESSAGE_ID = current_chat_pinned_msg.text.split('\n')[1].split(':')[1]
    PINNED_MESSAGE = current_chat_pinned_msg.text

    keyboard = [[InlineKeyboardButton("Insert records into chatbox", switch_inline_query_current_chat=PINNED_MESSAGE)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Click the button to edit the current records.\nOnce done, send the message!\n\n<b>(DO NOT REMOVE "@readers_tracker_bot"!!)</b>', reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    return EDITED

def edited(update, context):
    global PINNED_MESSAGE_ID, PINNED_MESSAGE

    user = update.message.from_user
    chat_id = update.message.chat_id

    user_input_message = update.message.text
    user_input_message = user_input_message.replace('@readers_tracker_bot', '')
    user_input_message.strip()
    logger.info(f"{user.username} edited the pinned message to '{user_input_message}'")

    context.bot.edit_message_text(user_input_message, chat_id, PINNED_MESSAGE_ID)
    update.message.reply_text('All done!!')

    return ConversationHandler.END

def cancel(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    logger.info(f'{user.username} cancelled the conversation')
    update.message.reply_text(
        'Request cancelled', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=ParseMode.HTML)

def main():
    updater = Updater(token=TOKEN)
    dp = updater.dispatcher

    start_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NUM_OF_DAYS: [MessageHandler(Filters.regex('^\d+$'),num_of_days)],
            NAME_OF_BOOKS: [MessageHandler(Filters.text & ~Filters.command,name_of_books), CommandHandler('skip',skip_books)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    edit_conv = ConversationHandler(
        entry_points=[CommandHandler('edit', edit)],
        states={
            EDITED: [MessageHandler(Filters.text & ~Filters.command,edited)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(CommandHandler('init',init))
    dp.add_handler(start_conv)
    dp.add_handler(CommandHandler('clock',clock))
    dp.add_handler(edit_conv)

    dp.add_error_handler(error_handler)

    # Webhook
    updater.start_webhook(listen='0.0.0.0',
                        port=os.environ.get('PORT',443),
                        url_path=TOKEN,
                        webhook_url='https://readers-16012022.herokuapp.com/' + TOKEN)

    # Manual
    # updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()