import decimal
from decimal import Decimal
from unittest import TestCase

from cryptalgo.coredata.holdings import Ledger, Account, FeeModel
from cryptalgo.coredata.trades import TradeSide



class TestLedger(TestCase):
    def test_add(self):
        l = Ledger(name="test")
        self.assertEqual(0, len(l.holdings))
        l.add('sym', 1.1)
        self.assertEqual(1, len(l.holdings))
        self.assertEqual(Decimal('1.1000'), l.holdings['sym'])
        with self.assertRaises(ValueError):
            l.add('sym', None)
        with self.assertRaises(ValueError):
            l.add(None, 1.1)


    def test_remove(self):
        l = Ledger(name="test")
        self.assertEqual(0, len(l.holdings))
        l.add('sym', 1.10)
        l.remove('sym', 1.00)
        self.assertEqual(Decimal('0.10000'), l.holdings['sym'])
        with self.assertRaises(ValueError):
            l.remove('sym', 1.0)

        with self.assertRaises(ValueError):
            l.remove('sym', None)
        with self.assertRaises(ValueError):
            l.remove(None, 1.1)


class TestFeeModel(FeeModel):

    def calculate_fee(self, symbol: str, amount: float, price: float, side: TradeSide) -> Decimal:
        return Decimal('2.99000')



class TestAccount(TestCase):
    def test_deposit_cash(self):
        a = Account()
        a.deposit_cash(100.00)
        self.assertEqual(Decimal('100.00000'), a.cash_ledger.holdings[a.default_currency])
        a.deposit_cash(2.95)
        self.assertEqual(Decimal('102.95000'), a.cash_ledger.holdings[a.default_currency])

        with self.assertRaises(ValueError):
            a.deposit_cash(None)

        with self.assertRaises(ValueError):
            a.deposit_cash(-1.0)


    def test_withdraw_cash(self):
        a = Account()
        a.deposit_cash(100.00)
        a.withdraw_cash(50.00)
        self.assertEqual(Decimal('50.00000'), a.cash_ledger.holdings[a.default_currency])
        a.withdraw_cash(44.99)
        self.assertEqual(Decimal('5.01000'), a.cash_ledger.holdings[a.default_currency])
        with self.assertRaises(ValueError):
            a.withdraw_cash(-100)

        with self.assertRaises(ValueError):
            a.withdraw_cash(None)

        with self.assertRaises(ValueError):
            a.withdraw_cash(-1.0)


    def test_add_shares(self):
        a = Account()
        a.add_shares('sym', 100.00)
        self.assertEqual(Decimal('100.00000'), a.securities_ledger.holdings['sym'])
        a.add_shares('sym', 5.99)
        self.assertEqual(Decimal('105.99000'), a.securities_ledger.holdings['sym'])

        with self.assertRaises(ValueError):
            a.add_shares(None, 1.0)
        with self.assertRaises(ValueError):
            a.add_shares('sym', -1.0)
        with self.assertRaises(ValueError):
            a.add_shares('sym', None)


    def test_remove_shares(self):
        a = Account()
        a.add_shares('sym', 100.00)
        a.remove_shares('sym', 4.99)
        self.assertEqual(Decimal('95.01000'), a.securities_ledger.holdings['sym'])
        a.remove_shares('sym', 5.01)
        self.assertEqual(Decimal('90.00000'), a.securities_ledger.holdings['sym'])

        with self.assertRaises(ValueError):
            a.remove_shares('sym', 1000.0)
        with self.assertRaises(ValueError):
            a.remove_shares(None, 1.0)
        with self.assertRaises(ValueError):
            a.remove_shares('sym', -1.0)
        with self.assertRaises(ValueError):
            a.remove_shares('sym', None)


    def test_buy_shares(self):
        # simple buys
        a = Account()
        a.deposit_cash(100.00)
        a.buy_shares('sym', 5.0, price=2.00)
        self.assertEqual(Decimal('5.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('90.00000'), a.cash_ledger.holdings[a.default_currency])
        a.buy_shares('sym', 1.0, price=3.00)
        self.assertEqual(Decimal('6.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('87.00000'), a.cash_ledger.holdings[a.default_currency])

        # buys with explicit fees
        a = Account()
        a.deposit_cash(100.00)
        a.buy_shares('sym', 5.0, price=2.00, fee=1.99)
        self.assertEqual(Decimal('5.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('88.01000'), a.cash_ledger.holdings[a.default_currency])
        a.buy_shares('sym', 1.0, price=3.00, fee=1.99)
        self.assertEqual(Decimal('6.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('83.02000'), a.cash_ledger.holdings[a.default_currency])

        # buys with trade model
        a = Account(default_trade_fee_model=TestFeeModel())
        a.deposit_cash(100.00)
        a.buy_shares('sym', 5.0, price=2.00)
        self.assertEqual(Decimal('5.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('87.01000'), a.cash_ledger.holdings[a.default_currency])
        a.buy_shares('sym', 1.0, price=3.00)
        self.assertEqual(Decimal('6.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('81.02000'), a.cash_ledger.holdings[a.default_currency])
        with self.assertRaises(ValueError):
            a.buy_shares('sym', 1000.0, 10000.00)
        with self.assertRaises(ValueError):
            a.buy_shares(None, 1.0, 1.0)
        with self.assertRaises(ValueError):
            a.buy_shares('sym', None, 1.0)
        with self.assertRaises(ValueError):
            a.buy_shares('sym', 1.0, None)
        with self.assertRaises(ValueError):
            a.buy_shares('sym', -1.0, -1.0)

    def test_sell_shares(self):

        # simple sells
        a = Account()
        a.deposit_cash(100.00)
        a.add_shares('sym', 10.0)
        a.sell_shares('sym', 5.0, price=2.00)
        self.assertEqual(Decimal('5.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('110.00000'), a.cash_ledger.holdings[a.default_currency])
        a.sell_shares('sym', 5.0, price=3.00)
        self.assertEqual(Decimal('0.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('125.00000'), a.cash_ledger.holdings[a.default_currency])

        # sells with explicit fees
        a = Account()
        a.deposit_cash(100.00)
        a.add_shares('sym', 10.0)
        a.sell_shares('sym', 5.0, price=2.00, fee=1.99)
        self.assertEqual(Decimal('5.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('108.01000'), a.cash_ledger.holdings[a.default_currency])
        a.sell_shares('sym', 5.0, price=3.00, fee=0.0)
        self.assertEqual(Decimal('0.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('123.01000'), a.cash_ledger.holdings[a.default_currency])

        # sells with trade model
        a = Account(default_trade_fee_model=TestFeeModel())
        a.deposit_cash(100.00)
        a.add_shares('sym', 10.0)
        a.sell_shares('sym', 5.0, price=2.00)
        self.assertEqual(Decimal('5.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('107.01000'), a.cash_ledger.holdings[a.default_currency])
        a.sell_shares('sym', 5.0, price=3.00)
        self.assertEqual(Decimal('0.00000'), a.securities_ledger.holdings['sym'])
        self.assertEqual(Decimal('119.02000'), a.cash_ledger.holdings[a.default_currency])

        with self.assertRaises(ValueError):
            a.sell_shares('sym', 1000.0, 10000.00)
        with self.assertRaises(ValueError):
            a.sell_shares(None, 1.0, 1.0)
        with self.assertRaises(ValueError):
            a.sell_shares('sym', None, 1.0)
        with self.assertRaises(ValueError):
            a.sell_shares('sym', 1.0, None)
        with self.assertRaises(ValueError):
            a.sell_shares('sym', -1.0, -1.0)
