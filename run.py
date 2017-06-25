from model.model import CreditContagionModel
from data.banks_1 import params

model = CreditContagionModel(params.__len__())
model.run_model(10)

model.export_report()
a = 0