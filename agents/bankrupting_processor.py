from agents.bank import Bank
from mesa import Agent

class BankruptingProcessor(Agent):
    def __init__(self, context):
        # context = {"banks": [bank_1, bank_2, ...]}
        self.context = context
        self.bankrupted_bank = []

    def set_context(self, context):
        self.context = context

    def add_bank(self, bank):
        self.bankrupted_bank.append(bank)

    def processing(self):
        while self.bankrupted_bank.__sizeof__() > 0:
            bank = self.bankrupted_bank.pop()
            banks = bank.other_agents(self.context["banks"])
            bank.after_bankrupting(banks)