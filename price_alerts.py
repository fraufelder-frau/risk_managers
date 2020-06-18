#!/usr/bin/env python
# coding: utf-8

import time
import pickle
import os
from datetime import datetime, timedelta, timezone
from bybit import bybit
from bitmex import bitmex
import requests
import json
import warnings
warnings.simplefilter("ignore")
import bravado.exception
import sys
from pathlib import Path
home = str(Path.home())+'/'
from bitmex_websocket import BitMEXWebsocket

def y_n_prompt():
    while True:
        y_n_responses = ['Yes', 'No']
        for (x, y) in enumerate(y_n_responses):
            print(str(x)+': '+y)
        response = y_n_responses[int(input('> '))]
        if response not in y_n_responses:
            print('Invalid Selection'+'\n')
            continue
        else:
            break
    return response

def usd_str(value):
    if '.' in str(value):
        if float(value) < 0:
            value = float(value)*-1
            value = '-'+"${:,.2f}".format(float(value))
        else:
            value = "${:,.2f}".format(float(value))
    else:
        if float(value) < 0:
            value = float(value)*-1
            value = '-'+"${:,}".format(float(value))
        else:
            value = "${:,}".format(float(value))
    return value

def list_prompt(initial_dialogue, list_to_view):
    while True:
        try:
            print(initial_dialogue)
            for k, v in enumerate(list_to_view):
                print(str(k)+': '+v)
            resp = list_to_view[int(input('> '))]
        except (IndexError, ValueError):
            print('Selection out of range of acceptable responses'+'\n')
            continue
        else:
            print('Selection: '+str(resp)+'\n')
            break
    return resp

def pickle_write(file, item):
    with open(file, 'wb') as handle:
        pickle.dump(item, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return print(file+' saved')

def pickle_load(file):
    with open(file, 'rb') as handle:
        temp = pickle.load(handle)
    return temp

#Telegram Text Alert
def telegram_sendText(bot_credentials, bot_message):
    bot_token = bot_credentials[0]
    bot_chatID = bot_credentials[1]
    send_text = 'https://api.telegram.org/bot'+bot_token+'/sendMessage?chat_id='+bot_chatID+'&text='+bot_message
    response = requests.get(send_text)
    return response.json()

def load_bot():
    file = home+'credentials.pickle'
    load_bot = False
    create_bot = False
    confirm_bot = False
    if os.path.exists(file):
        try:
            master_credentials = pickle_load(file)['bots']
        except KeyError:
            bot_name = str(input('Give your bot a name'+'\n'+'> '))
            master_credentials = pickle_load(file)
            master_credentials['bots'] = {bot_name: {'bot_token': None,
                                                     'bot_chatID': None}}
            create_bot = True
        else:
            master_credentials = pickle_load(file)
            load_bot = True
    else:
        bot_name = str(input('Give your bot a name'+'\n'+'> '))
        master_credentials = {'bots': {bot_name: {'bot_token': None,
                                                  'bot_chatID': None}}}
        create_bot = True
    if load_bot:
        bot_name = list(master_credentials['bots'].keys())
        bot_name = list_prompt('Choose your saved bot', bot_name+['New Bot'])
        if bot_name == 'New Bot':
            bot_name = str(input('Give your bot a name'+'\n'+'> '))
            create_bot = True
        else:
            credentials = master_credentials['bots'][bot_name]
            confirm_bot = True
    if confirm_bot:
        print('Confirm '+bot_name+' Connection')
        resp = y_n_prompt()
        if resp == 'No':
            print('Create new bot credentials')
            bot_name = str(input('Give your bot a name'+'\n'+'> '))
            create_bot = True            
    if create_bot:
        while True:
            bot_token = str(input('Input Your Telegram Bot API Key'+'\n'+'> '))
            bot_chatID = str(input('Input Your Telegram User ChatID'+'\n'+'> '))
            credentials = {'bots': {bot_name: {'bot_token': bot_token,
                                               'bot_chatID': bot_chatID}}}
            test_msg = telegram_sendText((bot_token, bot_chatID), 'Testing')['ok']
            if test_msg:
                print('\n'+'Confirm Test Message Receipt')
                resp = y_n_prompt()
                if resp == 'No':
                    print('Try Again'+'\n')
                    continue
                else:
                    print('Bot Credentials Verified'+'\n')
                    break
            else:
                print('Test Message Failed. Reenter Bot Credentials'+'\n')
                continue
    
        master_credentials['bots'].update(credentials['bots'])
        pickle_write(file, master_credentials)
    return master_credentials['bots'][bot_name]

def load_exchange(exchange):
    file = home+'credentials.pickle'
    load_connection = False
    create_connection = False
    confirm_connection = False
    if os.path.exists(file):
        try:
            master_credentials = pickle_load(file)[exchange]
        except KeyError:
            account_name = str(input('Input Your '+exchange+' Account Name'+'\n'+'> '))
            master_credentials = pickle_load(file)
            master_credentials[exchange] = {account_name: {'api_key': None,
                                                           'api_secret': None}}
            create_connection = True
        else:
            master_credentials = pickle_load(file)
            load_connection = True
    else:
        account_name = str(input('Input Your '+exchange+' Account Name'+'\n'+'> '))
        master_credentials = {exchange: {account_name: {'api_key': None,
                                                        'api_secret': None}}}
        create_connection = True
    if load_connection:
        while True:
            account_names = list(master_credentials[exchange].keys())
            account_name = list_prompt('Choose your saved '+exchange+' account', account_names+['New '+exchange+' Account'])
            if account_name == 'New '+exchange+' Account':
                account_name = str(input('Input Your '+exchange+' Account Name'+'\n'+'> '))
                create_connection = True
                break
            else:
                existing_options = ['Load', 'Edit', 'Delete']
                existing_selection = list_prompt('Choose action for '+account_name, existing_options)
                if existing_selection == 'Load':
                    credentials = master_credentials[exchange][account_name]
                    confirm_connection = True
                    break
                elif existing_selection == 'Edit':
                    create_connection = True
                    break
                elif existing_selection == 'Delete':
                    del master_credentials[exchange][account_name]
                    continue
    if confirm_connection:
        print('Confirm '+exchange+' Connection')
        resp = y_n_prompt()
        if resp == 'No':
            print('Create New '+exchange+' Credentials')
            account_name = str(input('Input Your '+exchange+' Account Name'+'\n'+'> '))
            create_connection = True
    if create_connection:
        while True:
            api_key = str(input('Input Your '+exchange+' API Key'+'\n'+'> '))
            api_secret = str(input('Input Your '+exchange+' API Secret'+'\n'+'> '))
            credentials = {exchange: {account_name: {'api_key': api_key,
                                                     'api_secret': api_secret}}}
            if exchange == 'Bitmex':
                    client = bitmex(test=False,api_key=api_key,
                                    api_secret=api_secret);
                    try:
                        print('\n'+'Testing '+exchange+' Credentials'+'\n')
                        client.User.User_getWalletHistory().result();
                    except bravado.exception.HTTPError:
                        print('Invalid '+exchange+' Credentials'+'\n')
                        continue
                    else:
                        print(exchange+' Credentials Verified'+'\n')
                        break
            elif exchange == 'Bybit':
                    client = bybit(test=False,api_key=api_key,
                                   api_secret=api_secret)
                    resp = client.APIkey.APIkey_info().result()[0]['ret_msg'];
                    if resp == 'invalid api_key':
                        print('Invalid '+exchange+' Credentials'+'\n')
                        continue
                    else:
                        print(exchange+' Credentials Verified'+'\n')
                        break
    
        master_credentials[exchange].update(credentials[exchange])
        pickle_write(file, master_credentials)
    return master_credentials[exchange][account_name]

def input_price(client, dialogue, valid_ticks):
    while True:
        print(dialogue)
        price = input('> ')
        print('\n')
        if '.' not in price and price[-1] not in str(valid_ticks) or '.' in price and price[-1] not in str({0, 5}):
            print('Invalid Tick Size'+'\n')
            continue
        else:
            price = float(price)
            break
    return price

def remove_duplicates(list_item):
    return list(dict.fromkeys(list_item))


while True:
    file = home+'credentials.pickle'
    exchanges = ['Bitmex', 'Exit']
    exchange = list_prompt('Choose an Exchange', exchanges)
    valid_ticks = list(range(10))
    if exchange == 'Exit':
        print('Exiting Program')
        break
    if os.path.exists(file) == False:
        load_exchange(exchange)
        load_bot()
    try:
        pickle_load(file)[exchange]
    except KeyError:
        print('No '+exchange+' Credentials on File')
        continue
    master_credentials = pickle_load(file)
    
    temp_exchange = {k:v for k,v in master_credentials.items() if k == exchange}
    accounts = list(temp_exchange[exchange].keys())
    account = list_prompt('Choose an '+exchange+' Account', accounts+['New Account'])
    if account == 'New Account':
        load_exchange(exchange)
        continue
    temp_exchange = {k:v for k,v in temp_exchange[exchange].items() if k == account}
    
    temp_bot = {k:v for k,v in master_credentials.items() if k == 'bots'}
    bot_accounts = list(temp_bot['bots'].keys())
    bot_account = list_prompt('Choose a Telegram Bot', bot_accounts+['New Bot'])
    if bot_account == 'New Bot':
        load_bot()
        continue
    temp_bot = {k:v for k,v in temp_bot['bots'].items() if k == bot_account}
    final_user = {exchange: dict(temp_exchange[account].items())}
    final_user['bot'] = temp_bot[bot_account]
    
    if exchange == 'Bitmex':
        client = bitmex(test=False,api_key=final_user[exchange]['api_key'],
                        api_secret=final_user[exchange]['api_secret']) 
    elif exchange == 'Bybit':
        client = bybit(test=False,api_key=final_user[exchange]['api_key'],
                       api_secret=final_user[exchange]['api_secret'])
    elif exchange == 'qTrade':
        client = QtradeAPI('https://api.qtrade.io', key=final_user[exchange]['api_key'])
    
    bot_credentials = (final_user['bot']['bot_token'],final_user['bot']['bot_chatID'])
    ws = BitMEXWebsocket(endpoint='wss://www.bitmex.com/realtime', symbol='XBTUSD', api_key=final_user['Bitmex']['api_key'], api_secret=final_user['Bitmex']['api_secret'])
    contracts = [x['symbol'] for x in ws.open_orders('')]
    contracts = remove_duplicates(contracts)
    symbol = list_prompt('Choose Contract to Track', contracts)
    ws = BitMEXWebsocket(endpoint='wss://www.bitmex.com/realtime', symbol=symbol, api_key=final_user['Bitmex']['api_key'], api_secret=final_user['Bitmex']['api_secret'])
    break


my_orders = [x for x in ws.open_orders('') if x['symbol'] == symbol]
alarm_types = []
if len([x['price'] for x in my_orders if x['price'] is not None and x['ordType'] != 'Limit']) > 0:
    alarm_types.append('Target')
if len([x['stopPx'] for x in my_orders if x['stopPx'] is not None and x['price'] is None]) > 0:
    alarm_types.append('Stop')
if len([x['price'] for x in my_orders if x['price'] is not None and x['ordType'] == 'Limit' and x['triggered'] == '']) > 0:
    alarm_types.append('Entry')
alarm = [list_prompt('Choose Alert Type', alarm_types+['All'])]
alarm_types = [x for x in alarm_types if x not in alarm]
if alarm[0] == 'All':
    alarm = alarm_types
else:
    while True:
        if len(alarm_types) > 0:
            print('Set Another Alarm?')
            resp = y_n_prompt()
            if resp == 'No':
                alarm = alarm[0]
                break
            else:
                alarm.append(list_prompt('Choose Alert Type', alarm_types))
                alarm_types = [x for x in alarm_types if x not in alarm]
                continue
        else:
            break

target_alarm = False
stop_alarm = False
entry_alarm = False
if 'Target' in alarm:
    target_price = [x['price'] for x in my_orders if x['price'] is not None and x['ordType'] != 'Limit'][0]
    target_alarm = True
if 'Stop' in alarm:
    stop_price = [x['stopPx'] for x in my_orders if x['stopPx'] is not None and x['price'] is None][0]
    stop_alarm = True
if 'Entry' in alarm:
    entry_price = [x['price'] for x in my_orders if x['price'] is not None and x['ordType'] == 'Limit' and x['triggered'] == ''][0]
    entry_alarm = True
current_price = ws.recent_trades()[-1]['price']
set_price = current_price
msg = symbol+' Alerts'+'\n'+'\n'+'Account: '+account+'\n'
msg += 'Current Price: '+usd_str(set_price)+'\n'
if entry_alarm:
    msg += 'Entry Alarm Set at '+usd_str(entry_price)+'\n'
if target_alarm:
    msg += 'Target Alarm Set at '+usd_str(target_price)+'\n'
if stop_alarm:
    msg += 'Stop Alarm Set at '+usd_str(stop_price)
telegram_sendText(bot_credentials, msg)
ws = BitMEXWebsocket(endpoint='wss://www.bitmex.com/realtime', symbol=symbol, api_key=final_user['Bitmex']['api_key'], api_secret=final_user['Bitmex']['api_secret'])
while target_alarm or stop_alarm or entry_alarm:
    current_price = ws.recent_trades()[-1]['price']
    if target_alarm:
        if target_price > set_price:
            if current_price >= target_price:
                telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Target Price Hit')
                target_alarm = False
        else:
            if current_price <= target_price:
                telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Target Price Hit')
                target_alarm = False
    if stop_alarm:
        if stop_price > set_price:
            if current_price >= stop_price:
                telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Stop Price Hit')
                stop_alarm = False
        else:
            if current_price <= stop_price:
                telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Stop Price Hit')
                stop_alarm = False
    if entry_alarm:
        if entry_price > set_price:
            if current_price >= entry_price:
                telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Entry Price Hit')
                msg = 'Updated '+symbol+' Position'+'\n'+'\n'
                msg += results_str(current_open(symbol))
                telegram_sendText(bot_credentials, msg);
                entry_alarm = False
        else:
            if current_price <= entry_price:
                telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Entry Price Hit')
                msg = 'Updated '+symbol+' Position'+'\n'+'\n'
                msg += results_str(current_open(symbol))
                telegram_sendText(bot_credentials, msg);
                entry_alarm = False
    time.sleep(0.2)
    continue
telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Alerts Cleared')

