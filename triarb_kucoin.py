# NOTE: first install this package for get kucoin python sdk: pip install kucoin-python
import requests
import json
import time
from kucoin.client import Market
from kucoin.client import Trade
from kucoin.client import User
# from google.colab import files
# uploaded = files.upload()


api_key = 'api_key'
api_secret = 'api_secret'
api_passphrase = 'api_passphrase'
coin_price_url = 'https://api.kucoin.com/api/v1/market/allTickers'

client = Trade(api_key, api_secret, api_passphrase, is_sandbox=False, url='')
user = User(api_key, api_secret, api_passphrase)
amount_dict = {
    "USDT": float(user.get_account('account_id')['available']),
    "BTC": float(user.get_account('account_id')['available']),
    'ETH': float(user.get_account('account_id')['available'])
}

market_data = Market(url='https://api.kucoin.com')

inc_list = {}
for x in market_data.get_symbol_list():
    inc_list[x['symbol']] = x['baseIncrement']

qinc_list = {}
for x in market_data.get_symbol_list():
    qinc_list[x['symbol']] = x['quoteIncrement']


def get_coin_arbitrage(url):
    return requests.get(url).json()


def collect_tradeables(json_obj):
    coin_list = []
    for coin in json_obj['data']['ticker']:
        coin_list.append(coin['symbol'])
    return coin_list


def structure_triangular_pairs(coin_list):
    triangular_pairs_list = []
    remove_duplicates_list = []
    pairs_list = coin_list[0:]

    for pair_a in pairs_list:
        pair_a_split = pair_a.split('-')
        a_base = pair_a_split[0]
        a_quote = pair_a_split[1]

        a_pair_box = [a_base, a_quote]

        for pair_b in pairs_list:
            pair_b_split = pair_b.split('-')
            b_base = pair_b_split[0]
            b_quote = pair_b_split[1]

            if pair_b != pair_a:
                if b_base in a_pair_box or b_quote in a_pair_box:

                    for pair_c in pairs_list:
                        pair_c_split = pair_c.split('-')
                        c_base = pair_c_split[0]
                        c_quote = pair_c_split[1]

                        if pair_c != pair_a and pair_c != pair_b:
                            combine_all = [pair_a, pair_b, pair_c]
                            pair_box = [a_base, a_quote, b_base, b_quote, c_base, c_quote]
                            counts_c_base = 0
                            for i in pair_box:
                                if i == c_base:
                                    counts_c_base += 1

                            counts_c_quote = 0
                            for i in pair_box:
                                if i == c_quote:
                                    counts_c_quote += 1

                            if counts_c_base == 2 and counts_c_quote == 2 and c_base != c_quote:
                                combined = pair_a + ',' + pair_b + ',' + pair_c
                                unique_item = ''.join(sorted(combine_all))
                                if unique_item not in remove_duplicates_list:
                                    match_dict = {
                                        "a_base": a_base,
                                        "b_base": b_base,
                                        "c_base": c_base,
                                        "a_quote": a_quote,
                                        "b_quote": b_quote,
                                        "c_quote": c_quote,
                                        "pair_a": pair_a,
                                        "pair_b": pair_b,
                                        "pair_c": pair_c,
                                        "combined": combined
                                    }
                                    triangular_pairs_list.append(match_dict)
                                    remove_duplicates_list.append(unique_item)
    return triangular_pairs_list


def get_price_for_t_pair(t_pair, prices_json):
    pair_a = t_pair['pair_a']
    pair_b = t_pair['pair_b']
    pair_c = t_pair['pair_c']

    for x in prices_json['data']['ticker']:
        if x['symbol'] == pair_a:
            pair_a_ask = float(x['sell'])
            pair_a_bid = float(x['buy'])
        if x['symbol'] == pair_b:
            pair_b_ask = float(x['sell'])
            pair_b_bid = float(x['buy'])
        if x['symbol'] == pair_c:
            pair_c_ask = float(x['sell'])
            pair_c_bid = float(x['buy'])

    return {
        "pair_a_ask": pair_a_ask,
        "pair_a_bid": pair_a_bid,
        "pair_b_ask": pair_b_ask,
        "pair_b_bid": pair_b_bid,
        "pair_c_ask": pair_c_ask,
        "pair_c_bid": pair_c_bid
    }


def cal_triangular_arb_surface_rate(t_pair, prices_dict):

    starting_amount = 1
    min_surface_rate = 0 
    surface_dict = {}
    contract_1 = ""
    contract_2 = ""
    contract_3 = ""
    direction_trade_1 = ""
    direction_trade_2 = ""
    direction_trade_3 = ""
    acquired_coin_t2 = 0
    acquired_coin_t3 = 0
    calculated = 0

    a_base = t_pair['a_base']
    a_quote = t_pair['a_quote']
    b_base = t_pair['b_base']
    b_quote = t_pair['b_quote']
    c_base = t_pair['c_base']
    c_quote = t_pair['c_quote']
    pair_a = t_pair['pair_a']
    pair_b = t_pair['pair_b']
    pair_c = t_pair['pair_c']

    a_ask = prices_dict['pair_a_ask']
    a_bid = prices_dict['pair_a_bid']
    b_ask = prices_dict['pair_b_ask']
    b_bid = prices_dict['pair_b_bid']
    c_ask = prices_dict['pair_c_ask']
    c_bid = prices_dict['pair_c_bid']

    direction_list = ['forward', 'reverse']
    for direction in direction_list:

        swap_1 = 0
        swap_2 = 0
        swap_3 = 0
        swap_1_rate = 0
        swap_2_rate = 0
        swap_3_rate = 0

        # Assume starting with a_base and swapping for a_quote
        if direction == "forward":
            swap_1 = a_base
            swap_2 = a_quote
            swap_1_rate = 1 / a_ask
            direction_trade_1 = "base_to_quote"

        # Assume starting with a_base and swapping for a_quote
        if direction == "reverse":
            swap_1 = a_quote
            swap_2 = a_base
            swap_1_rate = a_bid
            direction_trade_1 = "quote_to_base"

        # Place first trade
        contract_1 = pair_a
        acquired_coin_t1 = starting_amount * swap_1_rate

        """  FORWARD """
        # SCENARIO 1
        if direction == "forward":
            if a_quote == b_quote and calculated == 0:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_b

                if b_base == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                if b_base == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 2
        if direction == "forward":
            if a_quote == b_base and calculated == 0:
                swap_2_rate = 1 / b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_b

                if b_quote == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                if b_quote == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 3
        if direction == "forward":
            if a_quote == c_quote and calculated == 0:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_c

                if c_base == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                if c_base == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 4
        if direction == "forward":
            if a_quote == c_base and calculated == 0:
                swap_2_rate = 1 / c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_c

                if c_quote == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                if c_quote == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1




        """ REVERSE """
        # SCENARIO 1
        if direction == "reverse":
            if a_base == b_quote and calculated == 0:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_b

                if b_base == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                if b_base == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 2
        if direction == "reverse":
            if a_base == b_base and calculated == 0:
                swap_2_rate = 1 / b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_b

                if b_quote == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                if b_quote == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 3
        if direction == "reverse":
            if a_base == c_quote and calculated == 0:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_c

                if c_base == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                if c_base == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 4
        if direction == "reverse":
            if a_base == c_base and calculated == 0:
                swap_2_rate = 1 / c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_c

                if c_quote == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                if c_quote == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        """ PROFIT LOSS OUTPUT"""
        # Profit and Loss Calc
        profit_loss = acquired_coin_t3 - starting_amount
        profit_loss_perc = (profit_loss / starting_amount) * 100 if profit_loss != 0 else 0

        # Trade Description
        trade_description_1 = f"Start with {swap_1} of {starting_amount}. Swap at {swap_1_rate} for {swap_2} acquiring {acquired_coin_t1}."
        trade_description_2 = f"Swap {acquired_coin_t1} of {swap_2} at {swap_2_rate} for {swap_3} acquiring {acquired_coin_t2}."
        trade_description_3 = f"Swap {acquired_coin_t2} of {swap_3} at {swap_3_rate} for {swap_1} acquiring {acquired_coin_t3}."

        # Output Results
        if profit_loss_perc > min_surface_rate:
            surface_dict = {
                "swap_1": swap_1,
                "swap_2": swap_2,
                "swap_3": swap_3,
                "contract_1": contract_1,
                "contract_2": contract_2,
                "contract_3": contract_3,
                "direction_trade_1": direction_trade_1,
                "direction_trade_2": direction_trade_2,
                "direction_trade_3": direction_trade_3,
                "starting_amount": starting_amount,
                "acquired_coin_t1": acquired_coin_t1,
                "acquired_coin_t2": acquired_coin_t2,
                "acquired_coin_t3": acquired_coin_t3,
                "swap_1_rate": swap_1_rate,
                "swap_2_rate": swap_2_rate,
                "swap_3_rate": swap_3_rate,
                "profit_loss": profit_loss,
                "profit_loss_perc": profit_loss_perc,
                "direction": direction,
                "trade_description_1": trade_description_1,
                "trade_description_2": trade_description_2,
                "trade_description_3": trade_description_3
            }

            return surface_dict

    return surface_dict


def reformatted_orderbook(prices, c_direction):
    price_list_main = []
    if c_direction == 'base_to_quote':
        for p in prices['asks']:
            ask_price = float(p[0])
            adj_price = 1 / ask_price if ask_price != 0 else 0
            adj_quantity = float(p[1]) * ask_price
            price_list_main.append([adj_price, adj_quantity])
    if c_direction == 'quote_to_base':
        for p in prices['bids']:
            bid_price = float(p[0])
            adj_price = bid_price if bid_price != 0 else 0
            adj_quantity = float(p[1])
            price_list_main.append([adj_price, adj_quantity])
    return price_list_main


def calculate_acquired_coin(amount_in, orderbook):

    # Initialise Variables
    trading_balance = amount_in
    quantity_bought = 0
    acquired_coin = 0
    counts = 0

    for level in orderbook:

        # Extract the level price and quantity
        level_price = level[0]
        level_available_quantity = level[1]

        # Amount In is <= first level total_amount
        if trading_balance <= level_available_quantity:
            quantity_bought = trading_balance
            trading_balance = 0
            amount_bought = quantity_bought * level_price

        if trading_balance > level_available_quantity:
            quantity_bought = level_available_quantity
            trading_balance -= quantity_bought
            amount_bought = quantity_bought * level_price

        # accumulate acquired coin
        acquired_coin = acquired_coin + amount_bought

        # Exit Trade
        if trading_balance == 0:
            return acquired_coin

        # Exit if not enough order book levels
        counts += 1
        if counts == len(orderbook):
            return 0


def get_depth_from_orderbook(surface_arb):

    # Extract initial variables
    swap_1 = surface_arb['swap_1']
    swap_2 = surface_arb['swap_2']
    swap_3 = surface_arb['swap_3']
    starting_amount = 0
    starting_amount_dict = amount_dict

    if swap_1 in starting_amount_dict:
        starting_amount = starting_amount_dict[swap_1]

    # Define Pairs
    contract_1 = surface_arb['contract_1']
    contract_2 = surface_arb['contract_2']
    contract_3 = surface_arb['contract_3']

    # Define direction for trades
    contract_1_direction = surface_arb['direction_trade_1']
    contract_2_direction = surface_arb['direction_trade_2']
    contract_3_direction = surface_arb['direction_trade_3']

    # Get Order Book for First Trade Assessment
    url1 = f'https://api.kucoin.com/api/v1/market/orderbook/level2_20?symbol={contract_1}'
    depth_1_prices = get_coin_arbitrage(url1)['data']

    depth_1_reformatted_prices = reformatted_orderbook(depth_1_prices, contract_1_direction)

    url2 = f'https://api.kucoin.com/api/v1/market/orderbook/level2_20?symbol={contract_2}'
    depth_2_prices = get_coin_arbitrage(url2)['data']

    depth_2_reformatted_prices = reformatted_orderbook(depth_2_prices, contract_2_direction)

    url3 = f'https://api.kucoin.com/api/v1/market/orderbook/level2_20?symbol={contract_3}'
    depth_3_prices = get_coin_arbitrage(url3)['data']

    depth_3_reformatted_prices = reformatted_orderbook(depth_3_prices, contract_3_direction)

    # Get Acquired Coins
    acquired_coin_t1 = calculate_acquired_coin(starting_amount, depth_1_reformatted_prices)
    acquired_coin_t2 = calculate_acquired_coin(acquired_coin_t1, depth_2_reformatted_prices)
    acquired_coin_t3 = calculate_acquired_coin(acquired_coin_t2, depth_3_reformatted_prices)

    # Calculate Profit Loss Also Known As Real Rate
    profit_loss = acquired_coin_t3 - starting_amount
    real_rate_perc = (profit_loss / starting_amount) * 100 if profit_loss != 0 else 0

    if real_rate_perc > 0 and starting_amount != 0:
        return_dict = {
            "profit_loss": profit_loss,
            "real_rate_perc": real_rate_perc,
            "swap_1": swap_1,
            "contract_1": contract_1,
            "bid_con_1": depth_1_prices['bids'][0][0],
            "swap_2": swap_2,
            "contract_2": contract_2,
            "ask_con_2": depth_2_prices['asks'][0][0],
            "swap_3": swap_3,
            "contract_3": contract_3,
            "bid_con_3": depth_3_prices['bids'][0][0],
            "contract_1_direction": contract_1_direction,
            "contract_2_direction": contract_2_direction,
            "contract_3_direction": contract_3_direction
        }
        return return_dict
    else:
        return {}




def first_step():
    coin_json = get_coin_arbitrage(coin_price_url)

    return collect_tradeables(coin_json)


def second_step(coin_list):
    structured_list = structure_triangular_pairs(coin_list)

    with open('structured_triangular_pairs.json', 'w') as fp:
        json.dump(structured_list, fp)


def third_step():
    with open('structured_triangular_pairs.json') as json_file:
        structured_pairs = json.load(json_file)

    prices_json = get_coin_arbitrage(coin_price_url)

    for t_pair in structured_pairs:
        prices_dict = get_price_for_t_pair(t_pair, prices_json)
        surface_arb = cal_triangular_arb_surface_rate(t_pair, prices_dict)
        if len(surface_arb) > 0: 
            real_rate_arb = get_depth_from_orderbook(surface_arb)
            if len(real_rate_arb) != 0:
                print(real_rate_arb)


                """ START PART.
                This part, which is related to the execution of
                the transaction in the exchange, does not work properly and you
                will most likely lose money after its execution!
                I look forward to your comments to make this part profitable:)
                """
                first_amount1 = amount_dict[real_rate_arb['swap_1']]
                base_increment1 = len(str(inc_list[real_rate_arb['contract_1']])) - 2
                available_amount1 = f"{float(first_amount1):.{base_increment1}f}"
                final_amount1 = f"{float(available_amount1) - (float(available_amount1) * 1 / 100):.{base_increment1}f}"
                print(real_rate_arb['contract_1'])
                print({
                    'first_amount1': first_amount1,
                    'base_increment1': base_increment1,
                    'available_amount1': available_amount1,
                    'final_amount1': final_amount1
                })

                buy = client.create_market_order(real_rate_arb['contract_1'],
                                                 'sell',
                                                 size=final_amount1)
                
                #time.sleep(0.1)
                first_amount2 = 0
                for x in user.get_account_list():
                  if x['currency'] == real_rate_arb['swap_2'] and x['type'] == 'trade':
                    first_amount2 = x['available']
                #first_amount2 = float(final_amount1) * float(real_rate_arb['bid_con_1'])
                base_increment2 = len(str(qinc_list[real_rate_arb['contract_2']])) - 2
                available_amount2 = f"{float(first_amount2):.{base_increment2}f}"
                final_amount2 = f"{float(available_amount2) - (float(available_amount2) * 1 / 100):.{base_increment2}f}"
                print(real_rate_arb['contract_2'])
                print({
                    'first_amount2': first_amount2,
                    'base_increment2': base_increment2,
                    'available_amount2': available_amount2,
                    'final_amount2': final_amount2
                })

                sell = client.create_market_order(real_rate_arb['contract_2'],
                                                  'buy',
                                                  funds=final_amount2)

                #time.sleep(2)
                first_amount3 = 0
                for x in user.get_account_list():
                  if x['currency'] == real_rate_arb['swap_3'] and x['type'] == 'trade':
                    first_amount3 = x['available']
                #first_amount3 = float(final_amount2) * float(real_rate_arb['ask_con_2'])
                base_increment3 = len(str(inc_list[real_rate_arb['contract_3']])) - 2
                available_amount3 = f"{float(first_amount3):.{base_increment3}f}"
                final_amount3 = f"{float(available_amount3) - (float(available_amount3) * 1 / 100):.{base_increment3}f}"
                print(real_rate_arb['contract_3'])
                print({
                    'first_amount3': first_amount3,
                    'base_increment3': base_increment3,
                    'available_amount3': available_amount3,
                    'final_amount3': final_amount3
                })

                buy = client.create_market_order(real_rate_arb['contract_3'],
                                                 'sell',
                                                 size=final_amount3)
                amount_dict['BTC'] = float(user.get_account('account_id')['available'])
                print(float(amount_dict[real_rate_arb['swap_1']]), float(first_amount1))
                print(float(amount_dict[real_rate_arb['swap_1']]) - float(first_amount1))
                print('Profit Percentage:' ,f"{float(float(amount_dict[real_rate_arb['swap_1']]) * 100 / float(first_amount1)):.{10}f}")
                time.sleep(5)
                """
                This part, which is related to the execution of
                the transaction in the exchange, does not work properly and you
                will most likely lose money after its execution!
                I look forward to your comments to make this part profitable:)
                END OF PART. """



if __name__ == '__main__':
    # coin_list = first_step()
    # structured_pairs = second_step(coin_list)
    while True:
        third_step()
