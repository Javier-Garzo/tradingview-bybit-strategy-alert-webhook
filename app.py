from distutils.sysconfig import get_makefile_filename
import json, config
from flask import Flask, request, jsonify, render_template
from pybit import usdt_perpetual

app = Flask(__name__)

print("---------------------------------------")
session_auth = usdt_perpetual.HTTP(
    endpoint="https://api-testnet.bybit.com",
    api_key=config.API_KEY,
    api_secret=config.API_SECRET
), 

def order(sideIN, quantityIN, symbolIN):
    try:
        # check correct buy/sell order text
        if sideIN.lower() == "buy":
            sideIN = "Buy"
        elif sideIN.lower() == "sell":
            sideIN = "Sell"

        # check if order is in the same side (short/long) that the current position. Used for have only one order running on bybit
        position= session_auth[0].my_position(
            symbol=symbolIN
        )
        differentSide = False 
        if sideIN == "Sell" and position['result'][0]['size'] > 0: #Want sell and position is long
            differentSide = True
        elif sideIN == "Buy" and position['result'][1]['size'] > 0: #Want buy and position is short
            differentSide = True

        print("------------------------" +str(differentSide))
        # Call API bybit
        print(f"sending order Market - {sideIN} {quantityIN} {symbolIN}")
        order = session_auth[0].place_active_order(
            symbol=symbolIN,
            side=sideIN,
            order_type="Market",
            qty=quantityIN,
            time_in_force="GoodTillCancel",
            reduce_only=differentSide,
            close_on_trigger=differentSide
        )
        print(order)
        order = True
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order

@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/test')
def whatever():
    return 'this is a test rute'

@app.route('/webhook', methods=['POST'])
def webhook():
    #print(request.data)
    data = json.loads(request.data)
    
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }

    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contracts']
    ticker = data['ticker']
    order_response = order(side, quantity, ticker)

    if order_response:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")

        return {
            "code": "error",
            "message": "order failed"
        }