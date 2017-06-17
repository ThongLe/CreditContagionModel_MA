import unittest
from test import *

for test_class in ['BankTest']:
    suite = unittest.TestLoader().loadTestsFromTestCase(eval('BankTest'))
    unittest.TextTestRunner(verbosity=2).run(suite)