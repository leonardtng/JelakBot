import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler)

import requests
import csv

from credentials import TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

LOCATION, RESTAURANT, ORDER_RESTAURANT, ORDER_LOCATION, CUTOFF, VIEW, ORDERS_LIST = range(7)

LOCATION_LIST = ['Yale-NUS', 'Tembusu College', 'RC 4', 'College of Alice and Peter Tan', 'Temasek Hall']
RESTAURANT_LIST = ['McDonalds', 'Pastamania']

"""
START STREAM
"""

user_data = {
    "chat_id": "",
    "location": "",
    "restaurants": "",
}


def start(update, context):
    print('START')
    reply_keyboard = [LOCATION_LIST]

    update.message.reply_text(
        'Welcome to JelakBot! Please select your location',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

    return LOCATION


def location(update, context):
    global user_data
    user = update.message.from_user
    logger.info("%s chose: %s", user.first_name, update.message.text)

    update.message.reply_text(f'Location saved as {update.message.text}')

    user_data["chat_id"] = update.message['chat']["id"]
    user_data["location"] = update.message.text

    reply_keyboard = [RESTAURANT_LIST]
    update.message.reply_text(
        'Please select restaurants which you want to receive notifications for. You will only be notified when new '
        'requests are made for those those restaurants',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

    return RESTAURANT


def restaurant(update, context):
    global user_data
    user = update.message.from_user

    logger.info("%s chose: %s", user.first_name, update.message.text)

    with open('user_file.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',', fieldnames=('chat_id', 'location', 'restaurants'))
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            elif row["chat_id"] == str(user_data["chat_id"]):
                update.message.reply_text('You have already signed up!', reply_markup=ReplyKeyboardRemove())
                return ConversationHandler.END
            else:
                line_count += 1

    update.message.reply_text(f'Restaurant saved as {update.message.text}', reply_markup=ReplyKeyboardRemove())

    user_data["restaurants"] = update.message.text

    print(user_data)

    with open('user_file.csv', mode='a', newline='') as user_file:
        fieldnames = ['chat_id', 'location', 'restaurants']
        writer = csv.DictWriter(user_file, fieldnames=fieldnames)

        writer.writerow({"chat_id": user_data["chat_id"], "location": user_data["location"],
                         "restaurants": user_data["restaurants"]})

    return ConversationHandler.END


"""
ORDER STREAM
"""

order_data = {
    "order_restaurant": "",
    "cutoff": "",
    "poc_username": "",
}


def order(update, context):
    print('ORDER')
    reply_keyboard = [RESTAURANT_LIST]

    update.message.reply_text(
        'Please select the restaurant you are ordering from.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

    return ORDER_RESTAURANT


def order_restaurant(update, context):
    user = update.message.from_user

    logger.info("%s chose: %s", user.first_name, update.message.text)

    update.message.reply_text(f'Order Restaurant saved as {update.message.text}', reply_markup=ReplyKeyboardRemove())

    order_data["poc_username"] = update.message['chat']["username"]
    order_data["order_restaurant"] = update.message.text

    reply_keyboard = [LOCATION_LIST]

    update.message.reply_text(
        'Please select where you are delivering your food to.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

    return ORDER_LOCATION


def order_location(update, context):
    user = update.message.from_user

    logger.info("%s chose: %s", user.first_name, update.message.text)

    update.message.reply_text(f'Order Location saved as {update.message.text}', reply_markup=ReplyKeyboardRemove())

    order_data["order_location"] = update.message.text

    update.message.reply_text(
        'Please indicate the cutoff time which afterwards people can no longer join your order. ',
    )

    return CUTOFF


def cutoff(update, context):
    user = update.message.from_user

    logger.info("%s order cutoff: %s", user.first_name, update.message.text)

    update.message.reply_text(f'Order Cutoff saved as {update.message.text}')

    order_data["cutoff"] = update.message.text

    print(order_data)

    update.message.reply_text('Your order is saved as:\n'
                              f'Restuarant: {order_data["order_restaurant"]}\n'
                              f'Order Location: {order_data["order_location"]}\n'
                              f'Cutoff Time: {order_data["cutoff"]}\n'
                              f'POC Username: @{order_data["poc_username"]}\n'
                              'Please be reminded that your telegram handle will be shared.')

    with open('orders_file.csv', mode='a', newline='') as orders_file:
        fieldnames = ['order_restaurant', 'order_location', 'cutoff', 'poc_username']
        writer = csv.DictWriter(orders_file, fieldnames=fieldnames)

        writer.writerow(
            {"order_restaurant": order_data["order_restaurant"],
             "order_location": order_data["order_location"],
             "cutoff": order_data["cutoff"],
             "poc_username": order_data["poc_username"]})

    with open('user_file.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',', fieldnames=('chat_id', 'location', 'restaurants'))
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            elif (row["restaurants"] == order_data["order_restaurant"]) and (
                    row["location"] == order_data["order_location"]):
                send_text = 'https://api.telegram.org/bot' + TOKEN + '/sendMessage?chat_id=' + row[
                    "chat_id"] + '&text=' + \
                            'Someone is ordering food! See details here:\n' + f'Restuarant: {order_data["order_restaurant"]}\n' + \
                            f'Order Location: {order_data["order_location"]}\n' + f'Cutoff Time: {order_data["cutoff"]}\n' + \
                            f'POC Username: @{order_data["poc_username"]}\n' + \
                            'If you are keen on joining this order, contact the person at his/her telegram handle!'
                response = requests.get(send_text)
                logger.info(response.json())
                line_count += 1
            else:
                line_count += 1

    return ConversationHandler.END


'''
VIEW STREAM
'''


def view(update, context):
    print('VIEW')
    reply_keyboard = [LOCATION_LIST]

    update.message.reply_text(
        'Please select your current location.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

    return ORDERS_LIST


def orders_list(update, context):
    user = update.message.from_user
    logger.info("%s chose: %s", user.first_name, update.message.text)

    update.message.reply_text(f'Displaying orders from {update.message.text}:', reply_markup=ReplyKeyboardRemove())

    with open('orders_file.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',', fieldnames=('order_restaurant', 'order_location', 'cutoff',
                                                                         'poc_username'))
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            elif row["order_location"] == update.message.text:
                update.message.reply_text(f'Restuarant: {row["order_restaurant"]}\n' +
                                          f'Order Location: {row["order_location"]}\n' + f'Cutoff Time: {row["cutoff"]}\n' +
                                          f'POC Username: @{row["poc_username"]}\n' +
                                          'If you are keen on joining this order, contact the person at his/her telegram handle!'
                                          )
                line_count += 1
            else:
                line_count += 1

    return ConversationHandler.END


'''
HELPERS
'''


def help(update, context):
    help_message = ('Use these commands to navigate JelakBot:\n'
                    '/start - Set up your location and preferred restaurant which you would like notifications for\n'
                    '/order - Start an order\n'
                    '/view - View orders in your location'
                    )

    update.message.reply_text(help_message)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    conv_handler_signup = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        fallbacks=[],

        states={
            LOCATION: [MessageHandler(
                Filters.regex('^(Yale-NUS|Tembusu College|RC 4|College of Alice and Peter Tan|Temasek Hall)$'),
                location)],
            RESTAURANT: [MessageHandler(
                Filters.regex('^(McDonalds|Pastamania)$'),
                restaurant)],
        },
    )

    conv_handler_order = ConversationHandler(
        entry_points=[CommandHandler('order', order)],
        fallbacks=[],

        states={
            ORDER_RESTAURANT: [MessageHandler(
                Filters.regex('^(McDonalds|Pastamania)$'),
                order_restaurant)],
            ORDER_LOCATION: [MessageHandler(
                Filters.regex('^(Yale-NUS|Tembusu College|RC 4|College of Alice and Peter Tan|Temasek Hall)$'),
                order_location)],
            CUTOFF: [MessageHandler(Filters.text & ~Filters.command, cutoff)],
        },
    )

    conv_handler_view = ConversationHandler(
        entry_points=[CommandHandler('view', view)],
        fallbacks=[],

        states={
            ORDERS_LIST: [MessageHandler(
                Filters.regex('^(Yale-NUS|Tembusu College|RC 4|College of Alice and Peter Tan|Temasek Hall)$'),
                orders_list)],
        },
    )

    dp.add_handler(conv_handler_signup)
    dp.add_handler(conv_handler_order)
    dp.add_handler(conv_handler_view)
    dp.add_handler(CommandHandler("help", help))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
