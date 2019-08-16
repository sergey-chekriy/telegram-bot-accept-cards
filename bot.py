#!/usr/bin/env python3.7
from telegram.ext import Updater, Filters, CommandHandler, ConversationHandler, MessageHandler, CallbackContext, PicklePersistence, CallbackQueryHandler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from urllib.parse import unquote
import json
import os

import slot_machine

bot_persistence = PicklePersistence(filename='charity_bot_persistence')

class BillInfo(object):
    def __init__(self, bill_id, status, sum):
        self.bill_id  = bill_id
        self.status = status
        self.sum = sum



em_confirm = u'\U00002705'+'  '
em_charity = u'\U0001F4B3'+'  '
em_play    = u'\U0001F3AE'+'  '
em_points  = u'\U0001F3C1'+'  '
em_donate  = u'\U0001F4B8'+'  '
em_cashout = u'\U0001F3E6'+'  '
em_slot    = u'\U0001F3B0'+'  '
em_spin    = u'\U0001F3B2'+'  '
em_ch_bet  = u'\U0001F504'+'  '
em_rules   = u'\U0001F4DC'+'  '
em_mobile  = u'\U0001F4F1'+'  '
em_card    = u'\U0001F4B3'+'  '
em_qiwi    = u'\U0001F4B5'+'  '
em_back    = u'\U0001F519'+'  '
em_history = u'\U0001F4D6'+'  '
em_about   = u'\U00002139'+'  '


from QIWI_API import UserQiwi
from QIWI_API import QiwiError, TokenError, TransactionNotFound, WalletError, MapError, NotFoundAddress, CheckError, \
    WrongEmail, WrongNumber, TransactionError

VERSION = "Bot v1.0\nQiwiAPI v1.0"
LANGUAGE = "rus"
LANGUAGES = json.load(open("Languages.json"))
DIALOGS = LANGUAGES[LANGUAGE]
QIWI_KEYS = json.load(open("/root/bill-payments-node-js-sdk/server/qiwi_keys.json"))

print(QIWI_KEYS[0]["SEC_TOKEN"])
global_qiwi_user = UserQiwi(QIWI_KEYS[0]["SEC_TOKEN"])


def update_bills_info(update: Update, context: CallbackContext):
    for x in context.user_data["bill_list"]:
        x.status = global_qiwi_user.check_bill_id(x.bill_id)
    for x in context.user_data["bill_list"]:
        if (x.status == 'REJECTED' or x.status == 'EXPIRED'):
            context.user_data["bill_list"].remove(x)

def add_bills_points(update: Update, context: CallbackContext):
    for x in context.user_data["bill_list"]:
        if (x.status == 'PAID'):
            context.user_data["game_balance"] = context.user_data["game_balance"] + x.sum        
            context.user_data["bill_list"].remove(x)

def start(update: Update, context: CallbackContext):
    context.user_data["token"] = QIWI_KEYS[0]["SEC_TOKEN"] #update.message.text
    if not "bet" in context.user_data:
        context.user_data["bet"] = 20
    if not "game_balance" in context.user_data:
        context.user_data["game_balance"] = 0
    if not "bill_list" in context.user_data:
        context.user_data["bill_list"] = []    
    slot_machine.credit = context.user_data["game_balance"]
    slot_machine.cash = context.user_data["bet"]
    try:
        markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
        update.message.reply_text(DIALOGS["command"], reply_markup=markup)
        return 2
    except TokenError:
        print("token error")
        update.message.reply_text(DIALOGS["error"])
        start(update,context)



def my_points(update: Update, context: CallbackContext):
    update_bills_info(update,context)
    add_bills_points(update, context)
    update.message.reply_text(DIALOGS["game_balance"]+str(context.user_data["game_balance"]))
    return 2

def about(update: Update, context: CallbackContext):
    update.message.reply_text(DIALOGS["about_text"])
    return 2


def donate_one(update: Update, context: CallbackContext):
    url_donate = global_qiwi_user.topup(100)
    context.user_data["bill_list"].append(BillInfo(global_qiwi_user.active_bill,global_qiwi_user.active_bill_status,100))
    update_bills_info(update, context)
    #for x in context.user_data["bill_list"]:
    #    print(x.bill_id)
    #    print(x.status)
    #    print(x.sum)
    keyboard = [[InlineKeyboardButton(em_confirm + DIALOGS["donate_button_100"],url=url_donate )]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(DIALOGS["donate_description"], reply_markup=reply_markup)

def donate_five(update: Update, context: CallbackContext):
    url_donate = global_qiwi_user.topup(500)
    context.user_data["bill_list"].append(BillInfo(global_qiwi_user.active_bill,global_qiwi_user.active_bill_status,500))
    keyboard = [[InlineKeyboardButton(em_confirm + DIALOGS["donate_button_500"],url=url_donate )]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(DIALOGS["donate_description"], reply_markup=reply_markup)

def donate_ten(update: Update, context: CallbackContext):
    url_donate = global_qiwi_user.topup(1000)
    context.user_data["bill_list"].append(BillInfo(global_qiwi_user.active_bill,global_qiwi_user.active_bill_status,1000))
    keyboard = [[InlineKeyboardButton(em_confirm + DIALOGS["donate_button_1000"],url=url_donate )]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(DIALOGS["donate_description"], reply_markup=reply_markup)

def check_bill(update: Update, context: CallbackContext):
    update.message.reply_text(global_qiwi_user.check_bill())

def cancel_bill(update: Update, context: CallbackContext):
    update.message.reply_text(global_qiwi_user.cancel_bill())


def play(update: Update, context: CallbackContext):
    update_bills_info(update,context)
    add_bills_points(update, context)
    markup = ReplyKeyboardMarkup(play_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 22

def pay(update: Update, context: CallbackContext):
    if context.user_data["game_balance"] <= 50:
        markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
        update.message.reply_text(DIALOGS["low_balance"],reply_markup=markup)
        update.message.reply_text(DIALOGS["command"], reply_markup=markup)
        return 2

    context.user_data["check_type_rest"] = None
    markup = ReplyKeyboardMarkup(pay_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["hint_checkout"], reply_markup=markup)
    return 14


def enter_user_id(update: Update, context: CallbackContext):
    context.user_data["check_type_rest"] = "qiwi"
    update.message.reply_text(DIALOGS["enter user id"])
    return 17

def run_slot_machine(update: Update, context: CallbackContext):
    markup = ReplyKeyboardMarkup(game_keyboard, one_time_keyboard=False)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 23

def charity(update: Update, context: CallbackContext):
    markup = ReplyKeyboardMarkup(charity_keyboard, one_time_keyboard=False)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 25


def cashout(update: Update, context: CallbackContext):
    update.message.reply_text("cashout")
    return 22

def spin(update: Update, context: CallbackContext):
    slot_machine.credit = context.user_data["game_balance"]
    slot_machine.cash = context.user_data["bet"]
    

    if slot_machine.cash >= slot_machine.credit:
        update.message.reply_text("Ставка слишком высока!\nПонизь ставку, что бы продолжать игру.")
    elif slot_machine.credit >= 15 and slot_machine.credit - slot_machine.cash > 0:
        update.message.reply_text("Твоя ставка " + str(slot_machine.cash) + " !\n" +
                             slot_machine.play_game() + "\n"
                             + "Твой текущий счёт " + str(slot_machine.credit) + " \n"
                             )
        if slot_machine.flag:
           update.message.reply_text("Поздравляю, ты выиграл " + str(slot_machine.total_won) + " !")
        context.user_data["game_balance"] = slot_machine.credit
        context.user_data["bet"] = slot_machine.cash
    else:
        update.message.reply_text("Недостаточно средств для продолжения игры.\n" +
                                              "Увы, путник, на этом твоя игра закончена. Заходи в следующий раз!")

    return 23

def change_bet(update: Update, context: CallbackContext):
    update.message.reply_text("Текущая ставка " + str(context.user_data["bet"]) + "!")
    return 24

def get_bet(update: Update, context: CallbackContext):
    try:
        new_bet = int(update.message.text)
        context.user_data["bet"] = new_bet
        slot_machine.cash = context.user_data["bet"]
        update.message.reply_text("Новая ставка " + update.message.text + " принята!")
        return 23
    except:
        return 23 

def game_rules(update: Update, context: CallbackContext):
    update.message.reply_text("Приветствую тебя, игрок! Игра очень проста, каждый игровой ход проходит"
                                          " за 4 этапа:\n"
                         + "1) Нажатие на кнопку Потянуть рычаг! 💰 запускает автомат.\n Списывается ставка, отображается"
                         + " игровое поле 3x3 и по счастливой случайности (честный рандом) деньги либо проигрываются"
                         + " либо преумножаются.\n2) Если игрок хочет изменить ставку, то нужно всего лишь нажать "
                         + "на кнопку Изменить ставку или набрать нужное число в месте для набора сообщений.\n" +
                "3) Победными являются ряды из 3 одниковых элементов расположенных:\nпо горизонтали\n 🍒🍒 🍒\n"
                        +"по вертикали\n🍏\n🍏\n🍏\nпо диагонали\n7️⃣\n    7️⃣\n         7️⃣\n"
                         + "4) Выигрыш расчитывается из расчёта ставка * коэффициент категории:\n" +
                         " 7️⃣ - 4, 🍒 - 2, 🍏 - 1.5, 🔔- 1\nЕсли ставка превышает количество имеющихся средств,"
                         + " соотвествующее уведомление будет отображено на экране диалога.\n Удачной игры!")


    return 23



def get_user_id(update: Update, context: CallbackContext):
    context.user_data["user_id"] = update.message.text
    return 19


def mobile_phone(update: Update, context: CallbackContext):
    context.user_data["check_type_rest"] = "mobile"
    context.user_data["number"] = None
    markup = ReplyKeyboardMarkup(mobile_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 15


def enter_mobile(update: Update, context: CallbackContext):
    update.message.reply_text(DIALOGS["enter phone"])
    return 16


def get_mobile(update: Update, context: CallbackContext):
    context.user_data["number"] = update.message.text
    return 19

def to_card(update: Update, context: CallbackContext):
    context.user_data["check_type_rest"] = "card"
    update.message.reply_text(DIALOGS["enter card number"])
    return 21


def get_card_num(update: Update, context: CallbackContext):
    context.user_data["card_num"] = update.message.text
    context.user_data["card_type"] = global_qiwi_user.get_card_type(context.user_data["card_num"])
    return 19


def get_amount(update: Update, context: CallbackContext):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    amount = context.user_data["game_balance"]
    commission = (amount + 10 - 1) // 10
    if commission < 50:
        commission = 50
    print('commission='+str(commission))
    if context.user_data["check_type_rest"] == "mobile":
        if context.user_data["number"] is None:
            try:
                update.message.reply_text(global_qiwi_user.transaction_telephone(amount-commission),
                                          reply_markup=markup)
            except TransactionNotFound:
                update.message.reply_text(DIALOGS["tr_s_error"], reply_markup=markup)
            except WrongNumber:
                update.message.reply_text(DIALOGS["error number"], reply_markup=markup)
            except WalletError:
                update.message.reply_text(DIALOGS["error wallet"], reply_markup=markup)
            else:
                context.user_data["game_balance"]=0 
        else:
            try:
                update.message.reply_text(global_qiwi_user.transaction_telephone(amount-commission,
                                                                                  context.user_data["number"]),
                                          reply_markup=markup)
            except TransactionError:
                update.message.reply_text(DIALOGS["tr_s_error"], reply_markup=markup)
            except WrongNumber:
                update.message.reply_text(DIALOGS["error number"], reply_markup=markup)
            except WalletError:
                update.message.reply_text(DIALOGS["error wallet"], reply_markup=markup)
            else:
                context.user_data["game_balance"] = 0
    elif context.user_data["check_type_rest"] == "qiwi":
        try:
            update.message.reply_text(global_qiwi_user.transaction_qiwi(context.user_data["user_id"], amount-commission),
                                      reply_markup=markup)
        except TransactionError:
            update.message.reply_text(DIALOGS["tr_s_error"], reply_markup=markup)
        except WalletError:
            update.message.reply_text(DIALOGS["error wallet"], reply_markup=markup)
        else:
            context.user_data["game_balance"] = 0
    else:
        print('to card')
        print(context.user_data["card_num"])
        print(context.user_data["card_num"])
        print(amount-commission) 
        try:
            update.message.reply_text(global_qiwi_user.transaction_card(context.user_data["card_num"], context.user_data["card_type"], str(amount-commission)),
                                      reply_markup=markup)
        except TransactionError:
            update.message.reply_text(DIALOGS["tr_s_error"], reply_markup=markup)
        except WalletError:
            update.message.reply_text(DIALOGS["error wallet"], reply_markup=markup)
        except CardError:
            update.message.reply_text(DIALOGS["error card"], reply_markup=markup)
        else:
            context.user_data["game_balance"] = 0

    return 2


def wrong_answer(update: Update, context: CallbackContext):
    update.message.reply_text(DIALOGS["wrong_answer"])


def back(update: Update, context: CallbackContext):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 2


def stop(update: Update, context: CallbackContext):
    update.message.reply_text(DIALOGS["off"], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


button_back = [em_back+DIALOGS["back"]]

start_keyboard = [[em_charity+DIALOGS["charity"], em_points+DIALOGS["points"] ],
                  [em_play +DIALOGS["play"] ],
                  [em_about +DIALOGS["about"]  ] ]

pay_keyboard = [[em_mobile+DIALOGS["mobile phone"], em_qiwi+DIALOGS["qiwi user"], em_card+DIALOGS["card"]],
                button_back]

mobile_keyboard = [[
                   DIALOGS["enter phone"]],
                   button_back]

play_keyboard = [[em_slot+DIALOGS["slot machine"],  em_cashout+DIALOGS["cashout"]],
                button_back]

game_keyboard = [[em_spin+DIALOGS["spin"], em_ch_bet+DIALOGS["change bet"], em_rules+DIALOGS["game rules"]],
                button_back]

charity_keyboard = [[em_donate+DIALOGS["100 RUB"], em_donate+DIALOGS["500 RUB"], em_donate+DIALOGS["1000 RUB"]],
                button_back]


markup = None


def main():
    updater = Updater("xxx", persistence=bot_persistence, use_context=True)
    dp = updater.dispatcher
    j = updater.job_queue
    command_back = MessageHandler(Filters.regex("^{}$".format(em_back+DIALOGS["back"])), back)
    wrong_answer_hd = MessageHandler(Filters.text, wrong_answer)

    def job_donate(context):
        job = context.job
        print("donate check start")
        current_bal = global_qiwi_user.get_balance0()
        print(str(current_bal))
        #check balance, if balance > 1500, donate 100 vera, 100 rusfund 
        #if current_bal > 1500:
        #    global_qiwi_user.transaction_org('vera','100')
        #    global_qiwi_user.transaction_org('rusfund','100')
        

    job_minute = j.run_repeating(job_donate, interval=120, first=0)

	
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
                2: [ 
                    MessageHandler(Filters.regex("^{}$".format(em_charity+DIALOGS["charity"])), charity, pass_user_data=True),
                    MessageHandler(Filters.regex("^{}$".format(em_points+DIALOGS["points"])), my_points, pass_user_data=True),
                    MessageHandler(Filters.regex("^{}$".format(em_play+DIALOGS["play"])), play, pass_user_data=True),
                    MessageHandler(Filters.regex("^{}$".format(em_about+DIALOGS["about"])), about, pass_user_data=True),
                    wrong_answer_hd],


                14: [MessageHandler(Filters.regex("^{}$".format(em_qiwi+DIALOGS["qiwi user"])), enter_user_id),
                     MessageHandler(Filters.regex("^{}$".format(em_mobile+DIALOGS["mobile phone"])), mobile_phone, pass_user_data=True),
                     MessageHandler(Filters.regex("^{}$".format(em_card+DIALOGS["card"])), to_card, pass_user_data=True),
                     command_back, wrong_answer_hd],

                15: [ 
                     MessageHandler(Filters.regex("^{}$".format(DIALOGS["enter phone"])), enter_mobile),
                     command_back, wrong_answer_hd],

                16: [MessageHandler(Filters.text, get_mobile, pass_user_data=True)],
                17: [MessageHandler(Filters.text, get_user_id, pass_user_data=True)],
                19: [MessageHandler(Filters.text, get_amount, pass_user_data=True)], 
                21: [MessageHandler(Filters.text, get_card_num, pass_user_data=True)],

                22: [MessageHandler(Filters.regex("^{}$".format(em_slot+DIALOGS["slot machine"])), run_slot_machine, pass_user_data=True),
                     MessageHandler(Filters.regex("^{}$".format(em_cashout+DIALOGS["cashout"])), pay, pass_user_data=True),
                     command_back, wrong_answer_hd],

                23: [MessageHandler(Filters.regex("^{}$".format(em_spin+DIALOGS["spin"])), spin, pass_user_data=True),
                     MessageHandler(Filters.regex("^{}$".format(em_ch_bet+DIALOGS["change bet"])), change_bet, pass_user_data=True),
                     MessageHandler(Filters.regex("^{}$".format(em_rules+DIALOGS["game rules"])), game_rules, pass_user_data=True),
                     command_back, wrong_answer_hd],


                24: [MessageHandler(Filters.text, get_bet, pass_user_data=True)],

                25: [MessageHandler(Filters.regex("^{}$".format(em_donate+DIALOGS["100 RUB"])), donate_one, pass_user_data=True),
                     MessageHandler(Filters.regex("^{}$".format(em_donate+DIALOGS["500 RUB"])), donate_five, pass_user_data=True),
                     MessageHandler(Filters.regex("^{}$".format(em_donate+DIALOGS["1000 RUB"])), donate_ten, pass_user_data=True),
                     command_back, wrong_answer_hd]},


        fallbacks=[CommandHandler("stop", stop)]
    )

    dp.add_handler(conv_handler)

    print("Bot started...")

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
