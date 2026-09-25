import unittest
from backend.app.data import normalize_order_price,preflight_sl_tp

class PreflightGeometry(unittest.TestCase):
    def test_buy_accepts_bid_referenced_target_and_rejects_bad_direction(self):
        self.assertEqual(preflight_sl_tp('BUY',100.10,100.00,100.10,99.80,100.20,.10),[])
        failed=preflight_sl_tp('BUY',100.10,100.00,100.10,99.80,100.05,.10)
        self.assertIn('buy_tp_not_above_entry',failed)
        self.assertIn('buy_tp_inside_broker_minimum',failed)
    def test_sell_accepts_ask_referenced_target_and_rejects_bad_direction(self):
        self.assertEqual(preflight_sl_tp('SELL',100.00,100.00,100.10,100.20,99.80,.10),[])
        failed=preflight_sl_tp('SELL',100.00,100.00,100.10,100.20,100.05,.10)
        self.assertIn('sell_tp_not_below_entry',failed)
        self.assertIn('sell_tp_inside_broker_minimum',failed)
    def test_tick_normalization_uses_tick_grid_not_just_digits(self):
        self.assertEqual(normalize_order_price(100.024,.05,2),100.0)
        self.assertEqual(normalize_order_price(100.026,.05,2),100.05)

if __name__=='__main__':unittest.main()
