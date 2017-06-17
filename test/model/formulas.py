import unittest
from model.fomulas import *

class FormulasTest(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_size_score(self):
        Aj, A, I = 1, 1, 1
        self.assertEqual(size_score(Aj, A, I), 0)

        Aj, A, I = 4, [4, 9], [1, 1]
        self.assertEqual(size_score(Aj, A, I), -0.40546510810816438)