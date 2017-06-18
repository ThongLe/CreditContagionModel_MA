from agents.bank import Bank
from mesa import Agent

class BankruptingProcessor(Agent):
    def __init__(self, context={}):
        self.unique_id = 'BankruptingProcessor'
        # context = {"banks": [bank_1, bank_2, ...]}
        self.context = context
        self.bankrupted_bank = []

        self.cash = 0
        self.equity = 0
        self.deposit = 0
        self.external_asset = 0
        self.scheduled_repayment_amount = {}
        self.borrowings = {}
        self.lendings = {}
        self.bankrupted = None

    def set_context(self, context):
        self.context = context

    def add_bank(self, bank):
        self.bankrupted_bank.append(bank)

    def processing(self):
        while self.bankrupted_bank.__len__() > 0:
            bank = self.bankrupted_bank.pop()
            banks = bank.other_agents(self.context["banks"])
            bank.bankrupting(banks)

    def round_scheduled_repayment_amount(self):
        return None