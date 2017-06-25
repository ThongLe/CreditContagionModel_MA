from model.model import CreditContagionModel
from data.banks_1 import params

for i in range(2):
    model = CreditContagionModel(initial_bank=params.__len__(), test_case=i)
    model.run_model(10)

    model.export_report()

a = 0
