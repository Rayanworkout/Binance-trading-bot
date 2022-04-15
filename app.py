import json
import time
from flask import Flask
from flask import request
from flask import Response
import requests
from binance.client import Client

# {
#     "PASSWORD": "Bulbizarre",
#     "TOKEN": "ETH",
#     "SYMBOL": "ETHUSDT",
#     "SIDE": "BUY"
# }


app = Flask(__name__)


class Notify:
    def __init__(self, trade=False):
        self.trade = trade


notify = Notify()


def telegram_message(message):  # FUNCTION TO SEND MSG ON TELEGRAM GROUP
    requests.get("https://api.telegram.org/BOT_TOKEN/"
                 "sendMessage?chat_id=CHAT_ID&text={}".format(message))


def test_order(token, symbol, side):
    TEST_API_KEY = 'API_KEY'
    TEST_SECRET_KEY = 'API_KEY'

    test_client = Client(TEST_API_KEY, TEST_SECRET_KEY, testnet=True)
    usdt_balance = round(float(test_client.get_asset_balance(asset='USDT')['free']), 2)
    symbol_price = round(float(json.loads(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol="
                                                       f"{symbol}").text)['price']), 2)  # GET ASSET PRICE
    qty = round(usdt_balance * 0.1 / symbol_price, 5)
    try:
        if side == 'BUY' and usdt_balance > 140:
            test_client.create_order(symbol=symbol, side=test_client.SIDE_BUY,
                                     type=Client.ORDER_TYPE_MARKET,
                                     quantity=qty)

            # SENDING TRADE TO TELEGRAM
            telegram_message(f"🎯  ALERT {side} {token}\n\n"
                             f"{side} order was placed at {symbol_price} $ ✅\n\n Quantity: {qty} {token} \n\n - "
                             f"{round(qty * symbol_price)} $")
            return {
                'code': 'SUCCESS',
                'side': side,
                'token': token,
                'qty': qty
            }

        elif side == 'SELL':
            # CHECK IF WE HAVE SOME TOKEN TO SELL
            balance = float(test_client.get_asset_balance(asset=token)['free'])
            if balance > 0:
                test_client.create_order(symbol=symbol, side=test_client.SIDE_SELL,
                                         type=Client.ORDER_TYPE_MARKET,
                                         quantity=balance)

                # SENDING TRADE TO TELEGRAM
                telegram_message(f"🎯  ALERT {side} {token}\n\n"
                                 f"{side} order was placed at {symbol_price} $ ✅\n\n Quantity: {balance} \n\n"
                                 f"%2B {round(balance * symbol_price)} $")
            else:
                telegram_message(f"NO {token} TO SELL")

    except Exception as err:
        telegram_message(f'Could not place order {err} \n\n'
                         f'"{side} {qty} {symbol}"')


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    side = data['SIDE']
    token = data['TOKEN']
    symbol = data['SYMBOL']
    if data['PASSWORD'] != 'Bulbizarre':
        return {
            'code': 'error',
            'message': 'wrong password'
        }
    time.sleep(3)
    if not notify.trade:
        test_order(token, symbol, side)
        notify.trade = True
        return Response("Success.", status=200)
    else:
        notify.trade = False
        return Response('IN TRADE !', status=200)


if __name__ == '__main__':
    app.run()
