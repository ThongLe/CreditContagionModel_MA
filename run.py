from model.model import CreditContagionModel
from data.banks_1 import params
import numpy as np


    # for shock_rate in np.arange(0.01, 0.21, 0.01):
for i in range(1):
    shock_rate = 0.09
    model = CreditContagionModel(shock_type='Idiosyncratic_Shock_19_1', shocked_bank_number=19, initial_bank=params.__len__(), \
                                 test_case=i, shock_rate=shock_rate)
    model.run_model()

    model.export_report()

a = 0
