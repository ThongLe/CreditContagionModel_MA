from model.model import CreditContagionModel
from data.banks import params

model = CreditContagionModel(params.__len__())
model.run_model(5)
