import numpy as np

from mesa import Agent
import model.fomulas as fl

class Bank(Agent):
    def __init__(self, params):
        self.code = params.get("code", "")
        self.name = params.get("name", "")
        self.unique_id = self.name + "(" + str(self.code) + ")"

        # Liabilities
        self.repayment_amount_schedule = params.get("repayment_amount", {})
        self.short_term_debt_ratio = params.get("short_term_debt_ratio", 0)
        self.borrowings = params.get("borrowings", {})
        self.equity = params.get("equity", 0)
        self.deposit = params.get("deposit", 0)

        # Assets
        self.cash = params.get("cash", 0)
        self.lendings = params.get("lendings", {})
        self.external_asset = params.get("external_asset", {})
        self.is_bankrupt = False

        # ======
        self.equity_growth_rate = params.get("equity_growth_rate", 0.2)

        self.relation_score = {}
        self.size_score = {}
        self.relation_score = {}

        self.alpha = 0
        self.beta = 0

    def step(self, stage, banks):
        """ A single step of the agent. """
        if stage in [1, 2, 3]:
            return {
                1: self.stage_1,
                2: self.stage_2,
                3: self.stage_3
            }[stage](banks)

    # ===================================================================

    def total_borrowings(self):
        return sum(self.borrowings.values())

    def total_lendings(self):
        return sum(self.lendings.values())

    def total_asset(self):
        return self.cash + self.total_lendings() + self.external_asset

    def total_liability(self):
        return self.deposit + self.total_borrowings() + self.equity

    def check_balance_sheet_problem(self):
        return self.total_asset() == self.total_liability()

    # ===================================================================

    def pay(self, bank, amount):
        self.cash -= amount
        self.borrowings[bank.code] -= amount
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "paid" + " " + str(amount)

    def receive(self, bank, amount):
        self.cash += amount
        self.lendings[bank.code] -= amount
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "received" + " " + str(amount)

    def lend(self, bank, amount):
        self.cash -= amount
        self.lendings[bank.code] += amount
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "lend" + " " + str(amount)

    def borrow(self, bank, amount, scheduling_payment):
        self.cash += amount
        self.borrowings[bank.code] += amount
        self.repayment_amount_schedule[bank.code] = scheduling_payment
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "borrowed" + " " + str(amount)

    def change_deposit(self):
        print "change_deposit"

    def change_external_asset(self):
        print "change_external_asset"

    def change_equity(self):
        print "change_equity"

    def bankrupt(self):
        self.is_bankrupt = True
        print "bankrupt"

    def stage_1(self, banks):
        '''
        A model step. At stage 1, borrowing banks repay part of their loan to lending banks
        '''

        for bank in self.order_banks(banks):
            if self.borrowings[bank.code] > 0:
                amount = self.repayment_amount_schedule[bank.code].pop(0)
                if self.cash < amount:
                    self.bankrupt()
                    break
                self.pay(bank, amount)
                bank.receive(self, amount)

        # size_score
        self.size_score = {}

        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_1"

    def stage_2(self, banks):
        '''
        At stage 2, banks borrow and lend in the interbank market
        '''

        if self.need_a_loan():
            borrow_target_amount = self.calculate_borrow_target_amount()
            borrowed_amount = 0
            term = 1 if self.need_short_term_loan() else 4

            # 2.2. Ask for loan

            self.total_score = []

            other_banks = self.order_banks(banks)
            for bank in other_banks:
                self.total_score.append({bank:
                    fl.total_score(weight=[0.3, 0.7], score=[self.relation_score[bank.code], self.size_score[bank.code]])})
                bank_assets = [_.total_asset() for _ in other_banks]
                indicators = []
                self.size_score[bank] = fl.size_score(bank.total_asset(), bank_assets, indicators)

            bank_priority = sorted(self.total_score) # [{bank: 0.5}, ...]

            for bank_score in bank_priority:
                bank = bank_score.keys()[0]
                if bank.is_available_for_lendings():
                    real_borrowing_amount, scheduling_repayment = self.ask_for_a_loan(
                        bank, borrow_target_amount - borrowed_amount, term)
                    if real_borrowing_amount > 0:
                        self.borrow(bank, real_borrowing_amount, scheduling_repayment)
                        bank.lend(self, real_borrowing_amount)
                        borrowed_amount += real_borrowing_amount
                        if borrow_target_amount - borrowed_amount == 0:
                            break

            # relation_score
            self.relation_score = fl.relation_score(self.relation_score, borrowed_amount)

        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_2"

    def stage_3(self, banks):
        '''
        At stage 3, banks update other entries of the balance sheet
        '''
        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_3"

    # ===================================================================

    def is_available(self):
        return self.is_bankrupt

    def is_available_for_lendings(self):
        return True

    def update_short_term_debt_ratio(self):
        # To do
        self.short_term_debt_ratio = 0

    def ask_for_a_loan(self, bank, borrow_amount_target, term):
        available_amount = 0
        offer_amount = min(borrow_amount_target, available_amount)
        scheduling_repayment = [offer_amount / term for _ in range(term)] if offer_amount > 0 else []
        return offer_amount, scheduling_repayment

    def need_a_loan(self):
        return True if np.random.uniform(0, 1) < 0 else False

    def need_short_term_loan(self):
        return True if np.random.uniform(0, 1) < 0 else False

    def calculate_borrow_target_amount(self):
        return 0

    def order_banks(self, banks):
        return [bank for bank in banks if self.code != bank.code]
