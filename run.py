from model.model import CreditContagionModel
from data.banks_1 import params

for i in range(1):
    model = CreditContagionModel(shock_type='No shocked', shocked_bank_number=0, initial_bank=params.__len__(), test_case=i)
    model.run_model()

    model.export_report()

a = 0
