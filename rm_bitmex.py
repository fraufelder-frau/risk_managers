#!/usr/bin/env python
# coding: utf-8

import time
import pickle
import os
from datetime import datetime, timedelta, timezone
from sympy import symbols, Eq, solve
from bitmex import bitmex
import warnings
warnings.simplefilter("ignore")
import bravado.exception
import sys
from pathlib import Path
home = str(Path.home())+'/'
import decimal
import requests
import json


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

def btc_str(value):
    value = "{:,.8f}".format(float(value))
    return value

def pct_str(value):
    value = "{:,.2f}%".format(float(value)*100)
    return value

def btc_round(value):
    rounded_value = round(float(value), 8)
    return float(rounded_value)


def print_dict(dict_item):
    try:
        for x in range(len(dict_item)):
            for k, v in dict_item[x].items():
                print(str(k)+': '+str(v))
            print('\n')
    except KeyError:
        for k, v in dict_item.items():
            print(str(k)+': '+str(v))
        print('\n')
    return None


def list_to_dict(list_item):
    temp = {}
    for x,y in enumerate(list_item):
        temp[x+1] = y
    return temp


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


def results_str(dict_item):
    dict_msg = ''
    try:
        for x in range(len(dict_item)):
            for k, v in dict_item[x].items():
                dict_msg += k+': '+str(v)+'\n'
            dict_msg += '\n'
    except KeyError:
        for k, v in dict_item.items():
            dict_msg += k+': '+str(v)+'\n'
    return dict_msg


#Telegram Text Alert
def telegram_sendText(bot_credentials, bot_message):
    bot_token = bot_credentials[0]
    bot_chatID = bot_credentials[1]
    send_text = 'https://api.telegram.org/bot'+bot_token+'/sendMessage?chat_id='+bot_chatID+'&text='+bot_message
    response = requests.get(send_text)
    return response.json()

#Telegram Image Alert
def telegram_sendImage(bot_credentials, image):
    bot_token = bot_credentials[0]
    bot_chatID = bot_credentials[1]
    url = 'https://api.telegram.org/bot'+bot_token+'/sendPhoto';
    files = {'photo': open(image, 'rb')}
    data = {'chat_id' : bot_chatID}
    r = requests.post(url, files=files, data=data)
    return r

def telegram_sendFile(bot_credentials, file):
    bot_token = bot_credentials[0]
    bot_chatID = bot_credentials[1]
    url = 'https://api.telegram.org/bot'+bot_token+'/sendDocument';
    files = {'document': open(file, 'rb')}
    data = {'chat_id' : bot_chatID}
    r = requests.post(url, files=files, data=data)
    return r


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


def float_range(start, stop, step):
    while start < stop:
        yield float(start)
        start += decimal.Decimal(step)


def amend_position(symbol):
    new_stop = input_price(client, 'Enter New Stop Price or 0 to Skip', valid_ticks)
    new_target = input_price(client, 'Enter New Target Price or 0 to Skip', valid_ticks)
    my_orders = client.Order.Order_getOrders(filter = json.dumps({'open': 'true', 'symbol': symbol})).result()[0]
    try:
        stop = [x for x in my_orders if x['stopPx'] is not None and x['price'] is None and 'ReduceOnly' in x['execInst']][0]
    except IndexError:
        stop = None
    if stop is not None:
        stopID = stop['orderID']
    try:
        close = [x for x in my_orders if x['price'] is not None and 'ReduceOnly' in x['execInst']][0]
    except IndexError:
        close = None
    if close is not None:
        closeID = close['orderID']
    current_bitmex = client.Position.Position_get(filter=json.dumps({'symbol': symbol})).result()[0]
    qty = [x['currentQty'] for x in current_bitmex if x['symbol'] == symbol and x['isOpen'] == True][0]
    orderQty = qty*-1
    if new_stop != 0:
        if stop is not None:
            client.Order.Order_amend(orderID=stopID, stopPx=new_stop).result()
            print('Stop for '+symbol+' Amended to '+usd_str(new_stop))
        else:
            client.Order.Order_new(symbol=symbol, stopPx=new_stop, execInst=str('LastPrice, ReduceOnly'), orderQty=orderQty, ordType='Stop').result()
            print('Stop for '+symbol+' Set to '+usd_str(new_stop))
    else:
        print('Stop Unchanged')
    if new_target != 0 :
        if close is not None:
            client.Order.Order_amend(orderID=closeID, price=new_target).result()
            print('Target for '+symbol+' Amended to '+usd_str(new_target))
        else:
            client.Order.Order_new(symbol=symbol, price=new_target, execInst='ReduceOnly', orderQty=orderQty, ordType='Limit').result()
            print('Target for '+symbol+' Set to '+usd_str(new_target))
    else:
        print('Target Unchanged')
    if new_stop or new_target != 0:
        return print('\n'+'Updated Positions'+'\n'+'\n'+results_str(current_open(symbol)))
    else:
        return print('No Changes Made')


def close_position(symbol):
    resp = client.Position.Position_get(filter=json.dumps({'isOpen': True, 'symbol': symbol})).result()[0]
    if len(resp) == 0:
        return print('No '+symbol+' Position To Close')
    else:
        if resp['currentQty'] > 0:
            client.Order.Order_new(symbol=symbol, execInst='Close', side='Sell').result()
        else:
            client.Order.Order_new(symbol=symbol, execInst='Close', side='Buy').result()
        my_orders = client.Order.Order_getOrders(filter = json.dumps({'open': 'true', 'symbol': symbol})).result()[0]
        if len(my_orders) != 0:
            client.Order.Order_cancelAll(symbol=contract).result()
        return print(symbol+' Position Closed')


def new_trade_params(symbol):
    balance = client.User.User_getWallet().result()[0]['amount']/100000000
    symbol_data = [x for x in client.Instrument.Instrument_getActive().result()[0] if x['symbol'] == symbol][0]
    new_trade_data = {'contract': symbol,
                      'balance': balance,
                      'order_type': list_prompt('Choose Order Type for Entry', order_types),
                     'stop': input_price(client, 'Enter Stop Price', valid_ticks),
                     'target': input_price(client, 'Enter Target Price', valid_ticks),
                      'makerFee': symbol_data['makerFee'],
                      'takerFee': symbol_data['takerFee']}
    if new_trade_data['order_type'] == 'Limit':
        new_trade_data['entry'] = input_price(client, 'Enter Entry Price', valid_ticks)
    else:
        if new_trade_data['stop'] > new_trade_data['target']:
            new_trade_data['entry'] =  symbol_data['bidPrice']
        else:
            new_trade_data['entry'] =  symbol_data['askPrice']
    while True:
        try:
            risk = float(input('Account Percent Risk'+'\n'+'> '))
        except TypeError:
            print('Must be a number'+'\n')
            continue
        if risk == 0:
            risk = (new_trade_data['stop'] - new_trade_data['entry']) / new_trade_data['entry']
            break
        else:
            if risk not in percent_ticks:
                print('Invalid Entry'+'\n')
                continue
        break
    new_trade_data['risk'] = risk
    return new_trade_data


def new_trade(trade_params):
    contract = trade_params['contract']
    print('Updating Leverage to Cross'+'\n')
    client.Position.Position_updateLeverage(symbol=contract, leverage=0).result()
    if trade_params['side'] == 'Short':
        size = trade_params['size']*-1
    else:
        size = trade_params['size']
    entry = trade_params['entry']
    target = trade_params['target']
    stop = trade_params['stop']
    if trade_params['order_type'] == 'Market':
        client.Order.Order_cancelAll(symbol=contract).result()
        client.Order.Order_new(symbol=contract, orderQty=size, ordType='Market').result()
        client.Order.Order_new(symbol=contract, price=target, execInst='ReduceOnly', orderQty=(size*-1), ordType='Limit').result()
        client.Order.Order_new(symbol=contract, stopPx=stop, execInst=str('LastPrice, ReduceOnly'), orderQty=(size*-1), ordType='Stop').result()
    else:
        client.Order.Order_cancelAll(symbol=contract).result()
        client.Order.Order_new(symbol=contract, orderQty=size, price=entry).result()
        if target < entry:
            stop_limit_trigger = float(float(entry)+0.5)
        else:
            stop_limit_trigger = float(float(entry)-0.5)
        client.Order.Order_new(symbol=contract, stopPx=stop_limit_trigger, price=target, execInst=str('LastPrice, ReduceOnly'), orderQty=(size*-1), ordType='StopLimit').result()
        client.Order.Order_new(symbol=contract, stopPx=stop, execInst=str('LastPrice, ReduceOnly'), orderQty=(size*-1), ordType='Stop').result()
    return print('Orders Placed')


def position_size(trade_params):
    balance = client.User.User_getWallet().result()[0]['amount']/100000000
    entry_value = 1/trade_params['entry']
    stop_value = 1/trade_params['stop']
    x = symbols('x')
    base_risk = round(balance*trade_params['risk']/100, 8)
    if trade_params['order_type'] == 'Limit':
        entry_fee = trade_params['makerFee']
    else:
        entry_fee = trade_params['takerFee']
    if trade_params['entry'] > trade_params['stop']:
        trade_params['side'] = 'Long'
        eq1 = Eq(x*(entry_value-stop_value) + (base_risk-((x*entry_value*entry_fee)+(x*stop_value*trade_params['takerFee']))))
    else:
        trade_params['side'] = 'Short'
        eq1 = Eq(x*(entry_value-stop_value) - (base_risk-((x*entry_value*entry_fee)+(x*stop_value*trade_params['takerFee']))))
    size = solve(eq1)
    size = [ '%.0f' % elem for elem in size ]
    trade_params['size'] = int(size[0])
    return trade_params


def risk_dict(trade_params):
    temp = {'Contract': trade_params['contract'],
            'Account': account,
            'Balance': trade_params['balance'],
            'Side': trade_params['side'],
            'Size': trade_params['size'],
            'Entry': trade_params['entry'],
            'Stop': trade_params['stop'],
            'Target': trade_params['target'],
            'Risk': trade_params['risk'],
            'Reward': trade_params['reward']}
    return temp


def r_r(trade_params):
    trade_params['risk'] = pct_str(trade_params['risk']/100)+' | '+btc_str(risk_amount_XBT(trade_params))+' | '+usd_str(risk_amount_XBT(trade_params)*trade_params['stop'])
    trade_params['reward'] = pct_str(reward_amount_XBT(trade_params)/trade_params['balance'])+' | '+btc_str(reward_amount_XBT(trade_params))+' | '+usd_str(reward_amount_XBT(trade_params)*trade_params['target'])
    return trade_params


def risk_amount_XBT(trade_params):
    entry_value = 1/trade_params['entry']
    stop_value = 1/trade_params['stop']
    if trade_params['order_type'] == 'Limit':
        entry_fee = trade_params['makerFee']
    else:
        entry_fee = trade_params['takerFee']
    risk_amount = (trade_params['size']*(entry_value - stop_value))+((trade_params['size']*entry_value*entry_fee)+(trade_params['size']*stop_value*trade_params['takerFee']))
    risk_amount = float(round(risk_amount, 8))
    if trade_params['entry'] < trade_params['stop']:
        risk_amount = risk_amount*-1
    return risk_amount

def reward_amount_XBT(trade_params):
    entry_value = 1/trade_params['entry']
    target_value = 1/trade_params['target']    
    if trade_params['order_type'] == 'Limit':
        entry_fee = trade_params['makerFee']
    else:
        entry_fee = trade_params['takerFee']
    reward_amount = (trade_params['size']*(target_value - entry_value))-((trade_params['size']*entry_value*entry_fee)+(trade_params['size']*target_value*trade_params['makerFee']))
    reward_amount = float(round(reward_amount, 8))
    if trade_params['entry'] > trade_params['stop']:
        reward_amount = reward_amount*-1
    return reward_amount


def current_open(symbol):
    open_position = client.Position.Position_get(filter=json.dumps({'isOpen': True, 'symbol': symbol})).result()[0][0]
    if len(open_position) == 0:
        return print('No Open Position')
    else:
        my_orders = client.Order.Order_getOrders(filter = json.dumps({'open': 'true', 'symbol': symbol})).result()[0]
        try:
            stop_price = usd_str([x['stopPx'] for x in my_orders if x['stopPx'] is not None and x['price'] is None and 'ReduceOnly' in x['execInst']][0])
        except (IndexError, KeyError, TypeError):
            stop_price = 'No Stop Set'
        try:
            target_price = usd_str([x['price'] for x in my_orders if x['price'] is not None and 'ReduceOnly' in x['execInst']][0])
        except (IndexError, KeyError, TypeError):
            target_price = 'No Target Set'
        temp = {'Exchange': exchange,
                'Account': account,
                'Balance': client.User.User_getWallet().result()[0]['amount']/100000000,
                'Timestamp': datetime.strftime(datetime.utcnow(), '%m-%d-%Y %H:%M:%S'),
                'Contract': symbol
               }
        if open_position['currentQty'] < 0:
            temp['Side'] = 'Short'
        elif open_position['currentQty'] > 0:
            temp['Side'] = 'Long'
        temp['Size'] = open_position['currentQty']
        temp['Entry'] = usd_str(open_position['avgEntryPrice'])
        temp['Stop'] = stop_price
        temp['Target'] = target_price
        last_price = [y['lastPrice'] for y in requests.get('https://www.bitmex.com/api/v1/instrument/active').json() if symbol in y['symbol']][0]
        temp['LastPrice'] = usd_str(last_price)
        temp['UnrealisedPnl'] = btc_str(open_position['unrealisedPnl']/100000000)
        return temp


def all_open():
    data = client.Position.Position_get(filter=json.dumps({'isOpen': True})).result()[0]
    positions = []
    open_contracts = [x['symbol'] for x in data]
    open_contracts = remove_duplicates(open_contracts)
    if len(open_contracts) > 1:
        for x in open_contracts:
            positions.append(current_open(x))
    else:
        symbol = open_contracts[0]
        positions = current_open(symbol)
    return positions


def take_profit_order(symbol, take_profit):
    my_orders = client.Order.Order_getOrders(filter = json.dumps({'open': 'true', 'symbol': symbol})).result()[0]
    try:
        stop_order = [x for x in my_orders if x['stopPx'] is not None and x['price'] is None and 'ReduceOnly' in x['execInst']][0]
    except IndexError:
        stopID = None
    else:
        stop_price = stop_order['stopPx']
        stopID = stop_order['orderID']
    try:
        target_order = [x for x in my_orders if x['price'] is not None and 'ReduceOnly' in x['execInst']][0]
    except IndexError:
        targetID = None
    else:
        target_price = target_order['price']
        targetID = target_order['orderID']
    new_stop = input_price(client, 'Enter New Stop Price or 0 to Skip', valid_ticks)
    new_target = input_price(client, 'Enter New Target Price or 0 to Skip', valid_ticks)
    open_position = client.Position.Position_get(filter=json.dumps({'isOpen': True, 'symbol': symbol})).result()[0][0]
    take_profit_size = round(((open_position['currentQty']*(int(take_profit)/100))*-1), 0)
    client.Order.Order_new(symbol=symbol, orderQty=take_profit_size, ordType='Market').result()
    new_size = client.Position.Position_get(filter=json.dumps({'isOpen': True, 'symbol': symbol})).result()[0][0]['currentQty']
    if new_target != 0:
        target_exec_price = new_target
    elif new_target == 0 and targetID is not None:
        target_exec_price = target_price
    else:
        target_exec_price = None
    if target_exec_price is not None:
        client.Order.Order_new(symbol=symbol, price=exec_price, execInst='ReduceOnly', orderQty=(new_size*-1), ordType='Limit').result()
        print('Target for '+symbol+' Set to '+usd_str(new_target))
    if new_stop != 0:
        stop_exec_price = new_stop
    elif new_stop == 0 and stopID is not None:
        stop_exec_price = stop_price
    else:
        stop_exec_price = None
    if stop_exec_price is not None:
        client.Order.Order_amend(orderID=stopID, stopPx=stop_exec_price, orderQty=(new_size*-1)).result()
        print('Stop for '+symbol+' Set to '+usd_str(new_stop))
    return print('\n'+'Updated Positions'+'\n'+'\n'+results_str(current_open(symbol)))


def remove_duplicates(list_item):
    return list(dict.fromkeys(list_item))


def set_alerts():
    master_credentials = pickle_load(file)
    temp_bot = {k:v for k,v in master_credentials.items() if k == 'bots'}
    bot_accounts = list(temp_bot['bots'].keys())
    bot_account = list_prompt('Choose an Alert Bot', bot_accounts)
    temp_bot = {k:v for k,v in temp_bot['bots'].items() if k == bot_account}
    bot_credentials = (temp_bot[bot_account]['bot_token'], temp_bot[bot_account]['bot_chatID'])
    my_orders = client.Order.Order_getOrders(filter = json.dumps({'open': 'true'})).result()[0]
    if len(my_orders) == 0:
        set_alerts = False
    else:
        contracts = [x['symbol'] for x in my_orders if 'XBT' in x['symbol']]
        contracts = remove_duplicates(contracts)
        if len(contracts) == 0:
            set_alerts = False
        symbol = list_prompt('Choose Contract to Track', contracts)
        set_alerts = True
    if set_alerts:
        try:
            entry_order = [x for x in my_orders if x['price'] is not None and 'ReduceOnly' not in x['execInst']][0]
        except IndexError:
            entry_price = None
        else:
            entry_price = entry_order['price']
            entryID = entry_order['orderID']
        try:
            stop_order = [x for x in my_orders if x['stopPx'] is not None and x['price'] is None and 'ReduceOnly' in x['execInst']][0]
        except IndexError:
            stop_price = None
        else:
            stop_price = stop_order['stopPx']
            stopID = stop_order['orderID']
        try:
            target_order = [x for x in my_orders if x['price'] is not None and 'ReduceOnly' in x['execInst']][0]
        except IndexError:
            target_price = None
        else:
            target_price = target_order['price']
            targetID = target_order['orderID']
        alarm_types = []
        if entry_price is not None:
            alarm_types.append('Entry')
        if stop_price is not None:
            alarm_types.append('Stop')
        if target_price is not None:
            alarm_types.append('Target')
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
        if 'Entry' in alarm:
            entry_alarm = True
        if 'Stop' in alarm:
            stop_alarm = True
        if 'Target' in alarm:
            target_alarm = True
        current_price = [x['lastPrice'] for x in requests.get('https://www.bitmex.com/api/v1/instrument/active').json() if x['symbol'] == symbol][0]
        msg = symbol+' Alerts'+'\n'+'\n'+'Account: '+account+'\n'
        msg += 'Current Price: '+usd_str(current_price)+'\n'
        if entry_alarm:
            msg += 'Entry Alarm Set at '+usd_str(entry_price)+'\n'
        if target_alarm:
            msg += 'Target Alarm Set at '+usd_str(target_price)+'\n'
        if stop_alarm:
            msg += 'Stop Alarm Set at '+usd_str(stop_price)
        telegram_sendText(bot_credentials, msg)
        while target_alarm or stop_alarm or entry_alarm:
            try:
                my_orders = client.Order.Order_getOrders(reverse = True, filter = json.dumps({'symbol': symbol})).result()[0]
            except bravado.exception.HTTPBadRequest:
                continue
            if len(my_orders) == 0:
                target_alarm = False
                stop_alarm = False
                entry_alarm = False
            if target_alarm:
                target_status = [x for x in my_orders if x['orderID'] == targetID][0]['ordStatus']
                if target_status == 'Filled':
                    telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Target Order Filled')
                    target_alarm = False
                elif target_status == 'Canceled':
                    telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Target Order Canceled')
                    target_alarm = False
            if stop_alarm:
                stop_status = [x for x in my_orders if x['orderID'] == stopID][0]['ordStatus']
                if stop_status == 'Filled':
                    telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Stop Order Filled')
                    stop_alarm = False
                elif stop_status == 'Canceled':
                    telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Stop Order Canceled')
                    stop_alarm = False
            if entry_alarm:
                entry_status = [x for x in my_orders if x['orderID'] == entryID][0]['ordStatus']
                if entry_status == 'Filled':
                    telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Entry Order Filled')
                    entry_alarm = False
                elif entry_status == 'Canceled':
                    telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Entry Order Canceled')
                    entry_alarm = False
            time.sleep(1)
        telegram_sendText(bot_credentials, 'Account: '+account+'\n'+symbol+' Alerts Cleared')
        return print('Account: '+account+'\n'+symbol+' Alerts Cleared')
    else:
        return print('No Open Orders')


print('Begin Risk Manager')
while True:
    file = home+'credentials.pickle'
    exchanges = ['Bitmex', 'Exit']
    exchange = list_prompt('Choose an Exchange', exchanges)
    if exchange == 'Exit':
        if master_credentials:
            print('Set Price Alerts?')
            resp = y_n_prompt()
            if resp == 'Yes':
                try:
                    set_alerts()
                except KeyboardInterrupt:
                    print('Alarms Canceled')
            else:
                print('Exiting Program')
                break
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
    bot = False
    print('Use '+exchange+' Bot?')
    resp = y_n_prompt()
    if resp == 'Yes':
        temp_bot = {k:v for k,v in master_credentials.items() if k == 'bots'}
        bot_accounts = list(temp_bot['bots'].keys())
        bot_account = list_prompt('Choose a Telegram Bot', bot_accounts+['New Bot'])
        if bot_account == 'New Bot':
            load_bot()
            continue
        temp_bot = {k:v for k,v in temp_bot['bots'].items() if k == bot_account}
        bot = True
    
    final_user = {exchange: dict(temp_exchange[account].items())}
    if bot:
        final_user['bot'] = temp_bot[bot_account]
    if exchange == 'Bitmex':
        client = bitmex(test=False,api_key=final_user[exchange]['api_key'],
                        api_secret=final_user[exchange]['api_secret']) 
    elif exchange == 'Bybit':
        client = bybit(test=False,api_key=final_user[exchange]['api_key'],
                       api_secret=final_user[exchange]['api_secret'])
    elif exchange == 'qTrade':
        client = QtradeAPI('https://api.qtrade.io', key=final_user[exchange]['api_key'])
    if bot == True:
        bot_credentials = (final_user['bot']['bot_token'],final_user['bot']['bot_chatID'])
    
    order_types = ['Market', 'Limit']
    valid_ticks = list(range(10))
    percent_ticks = list(float_range(0, 100, '0.01'))[1:]+[100.00]
    null_orders = ['Deactivated', 'Cancelled', 'Filled']

    if exchange == 'Bitmex':
        while True:
            data = client.Position.Position_get(filter=json.dumps({'isOpen': True})).result()[0]
            step1_options = ['Change Exchange/Account', 'Plan New Trade']
            if len(data) > 0:
                step1_options.append('View/Manage Open Positions')
            step1 = list_prompt('Choose Starting Option', step1_options)
            if step1 == 'Change Exchange/Account':
                break
            elif step1 == 'View/Manage Open Positions':
                my_positions = all_open();
                print('\n'+'Your Bitmex Open Positions'+'\n')
                active_contracts = []
                if type(my_positions) == list:
                    for x in range(len(my_positions)):
                        print_dict(my_positions[x])
                        active_contracts.append(my_positions[x]['Contract'])
                else:
                    print_dict(my_positions)
                    active_contracts.append(my_positions['Contract'])
                step2_options = ['Close Position', 'Amend Orders', 'Take Profit', 'Return to Start']
                step2 = list_prompt('Choose an Option', step2_options)
                if step2 != 'Return to Start':
                    contract_to_view = list_prompt('Choose a Position to Manage', active_contracts)
                    if contract_to_view == 'Return to Start':
                        print('\n')
                        continue
                    if step2 == 'Close Position':
                        print('\n')
                        close_position(contract_to_view)
                        continue
                    elif step2 == 'Amend Orders':
                        print('\n')
                        amend_position(contract_to_view)
                        if bot:
                            msg = 'Updated '+contract_to_view+' Position\n\n'
                            msg += results_str(current_open(contract_to_view))
                            telegram_sendText(bot_credentials, msg);
                        continue
                    elif step2 == 'Take Profit':
                        print('\n')
                        while True:
                            try:
                                take_profit = float(input('Percent of '+contract_to_view+' position to close'+'\n'+'> '))
                            except TypeError:
                                print('Must be a number'+'\n')
                                continue
                            if take_profit == 0:
                                break
                            else:
                                if take_profit not in percent_ticks:
                                    print('Invalid Entry'+'\n')
                                    continue
                                break
                        if take_profit == 0:
                            continue
                        else:
                            take_profit_order(contract_to_view, take_profit)
                            if bot:
                                msg = 'Updated '+contract_to_view+' Position\n\n'
                                msg += results_str(current_open(contract_to_view))
                                telegram_sendText(bot_credentials, msg);
                            continue

            elif step1 == 'Plan New Trade':
                bitmex_data = requests.get('https://www.bitmex.com/api/v1/instrument/active').json()
                contracts = [x['symbol'] for x in bitmex_data if 'XBT' in x['symbol']]
                contract = list_prompt('Choose Contract to Trade', contracts)
                new_trade_data = new_trade_params(contract);
                new_trade_data = position_size(new_trade_data);
                new_trade_data = r_r(new_trade_data)
                final_dict = risk_dict(new_trade_data)
                print_dict(final_dict)
                print('Execute Trade?'+'\n'+'WARNING: ALL EXISTING OPEN POSITIONS AND ORDERS FOR THIS CONTRACT WILL BE CLOSED')
                resp = y_n_prompt()
                if resp == 'No':
                    print('TRADE NOT EXECUTED'+'\n')
                    continue
                else:
                    close_position(contract)
                    new_trade(new_trade_data)
                    if bot:
                        if new_trade_data['order_type'] == 'Market':
                            msg = 'Updated '+contract+' Position\n\n'
                            msg+= results_str(current_open(contract))
                        else:
                            msg = 'Updated '+contract+' Planned Trade\n\n'
                            msg+= results_str(final_dict)
                        telegram_sendText(bot_credentials, msg);
                    continue

