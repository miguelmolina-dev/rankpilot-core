import unittest
from src.strategies.legal500 import Legal500Strategy
from src.strategies.chambers import ChambersStrategy

class TestStrategies(unittest.TestCase):
    def test_legal500_strategy_init(self):
        strategy = Legal500Strategy()
        self.assertIsNotNone(strategy.config)
        self.assertEqual(strategy.config.get("name"), "Legal500 US")

        gaps = strategy.audit({})
        self.assertTrue(len(gaps) > 0)

    def test_chambers_strategy_init(self):
        strategy = ChambersStrategy()
        self.assertIsNotNone(strategy.config)
        self.assertEqual(strategy.config.get("name"), "Chambers Global")

        gaps = strategy.audit({})
        self.assertTrue(len(gaps) > 0)
