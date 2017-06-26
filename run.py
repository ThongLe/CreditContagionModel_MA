from model.model import CreditContagionModel
from data.banks_1 import params

for i in range(10):
    model = CreditContagionModel(shock_type='Idiosyncratic Shock', shocked_bank_number=1, initial_bank=params.__len__(), test_case=i)
    model.run_model()

    model.export_report()

a = 0
