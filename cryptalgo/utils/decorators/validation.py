def requires_amount(func):
    def wrapper(*args, **kwargs):
        amount = None
        if len(args) >= 2:
            amount = args[1]
        elif 'amount' in kwargs:
            amount = kwargs['amount']
        if amount is None or amount < 0.0:
            raise ValueError("amount must be passed and be positive; amount={0}".format(amount))
        func(*args, **kwargs)


    return wrapper



def requires_symbol_and_amount(func):
    def wrapper(*args, **kwargs):
        symbol = None
        if len(args) >= 2:
            symbol = args[1]
        elif 'symbol' in kwargs:
            symbol = kwargs['symbol']
        if symbol is None or symbol == '':
            raise ValueError("symbol must be passed and be non-empty; symbol={0}".format(symbol))

        amount = None
        if len(args) >= 3:
            amount = args[2]
        elif 'amount' in kwargs:
            amount = kwargs['amount']
        if amount is None or amount < 0.0:
            raise ValueError("amount must be passed and be positive; amount={0}".format(amount))

        func(*args, **kwargs)


    return wrapper



def requires_symbol_amount_and_price(func):
    def wrapper(*args, **kwargs):
        price = None
        if len(args) >= 4:
            price = args[3]
        elif 'price' in kwargs:
            price = kwargs['price']
        if price is None or price < 0.0:
            raise ValueError("price must be passed and be positive; price={0}".format(price))

        func(*args, **kwargs)


    symbol_amount_wrapper = requires_symbol_and_amount(wrapper)
    return symbol_amount_wrapper