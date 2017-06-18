from agents.bank import Bank
from mesa import Agent

class BankruptingProcessor(Agent):
    def __init__(self, context={}):
        self.unique_id = 'BankruptingProcessor'
        # context = {"banks": [bank_1, bank_2, ...]}
        self.context = context
        self.bankrupted_bank = []

        self.cash = None
        self.equity = None
        self.deposit = None
        self.external_asset = None
        self.scheduled_repayment_amount = None
        self.borrowings = None
        self.lendings = None

    def set_context(self, context):
        self.context = context

    def add_bank(self, bank):
        self.bankrupted_bank.append(bank)

    def processing(self):
        while self.bankrupted_bank.__len__() > 0:
            bank = self.bankrupted_bank.pop()
            banks = bank.other_agents(self.context["banks"])
            bank.bankrupting(banks)