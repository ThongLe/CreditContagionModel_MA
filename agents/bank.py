import numpy as np

from mesa import Agent
import model.fomulas as fl
import math
from data.contanst import *

class Bank(Agent):
    def __init__(self, params):
        self.code = params.get("code", "")
        self.unique_id = self.code

        self.term = LOAN_TERM

        # Liabilities
        liability = params.get("liability", {})
        self.equity = liability.get("equity", 0)
        self.deposit = liability.get("deposit", 0)
        self.borrowings = params.get("borrowings", {}) # self.total_borrowings() == liability["total"] - self.equity - self.deposit

        # Assets
        asset = params.get("asset", {})
        self.cash = asset.get("cash", 0)
        self.external_asset = asset.get("external_asset", 0)
        self.lendings = params.get("lendings", {})   # self.total_lendings() == asset["total"] - self.cash - self.external_asset

        self.scheduled_repayment_amount = self.init_scheduled_payment(self.term)

        self.short_term_lending_rate = params.get("short_term_lending_rate", 0)
        self.short_term__rate = params.get("short_term_borrowing_rate", 0)

        self.growth_rate = params.get("growth_rate", {"deposit":        {"mean": 0, "var": 0},
                                                      "external_asset": {"mean": 0, "var": 0},
                                                      "equity":         {"mean": 0, "var": 0}})

        self.borrowing_target_rate = params.get("borrowing_target_rate", 0)
        self.lending_target_rate = params.get("lending_target_rate", 0)

        # ======

        self.borrowing_target_amount = 0
        self.lending_target_amount = 0
        self.bankrupted = False

        self.relation_score = fl.relation_score(0, self.total_borrowings())
        self.size_score = {}
        self.total_score = {}

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
        self.borrowings[bank] -= amount
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "paid" + " " + str(amount)

    def receive(self, bank, amount):
        self.cash += amount
        self.lendings[bank] -= amount
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "received" + " " + str(amount)

    def lend(self, bank, amount):
        self.cash -= amount
        self.lendings[bank] += amount
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "lend" + " " + str(amount)

    def borrow(self, bank, amount, scheduled_payment):
        self.cash += amount
        self.borrowings[bank] += amount
        self.update_scheduled_payment(bank, scheduled_payment)
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "borrowed" + " " + str(amount)

    def update_deposit(self):
        self.deposit *= math.exp(self.deposit_growth_rate())
        print "updated_deposit"

    def update_external_asset(self):
        self.external_asset *= math.exp(self.external_asset_growth_rate())
        print "updated_external_asset"

    def update_equity(self):
        self.equity *= (1 + self.equity_growth_rate())
        print "updated_equity"

    def bankrupt(self):
        self.bankrupted = True
        print "bankrupted"

    def stage_1(self, banks):
        '''
        A model step. At stage 1, borrowing banks repay part of their loan to lending banks
        '''
        self.update_deposit()
        self.update_borrowing_target_amount()
        self.update_lending_target_amount()
        self.update_external_asset()
        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_1"

    def stage_2(self, banks):
        '''
        At stage 2, banks borrow and lend in the interbank market
        '''
        bank_assets = [_.total_asset() for _ in banks]
        indicators = []
        self.size_score = {bank: fl.size_score(bank.total_asset(), bank_assets, indicators) for bank in banks}

        if self.need_a_loan():
            borrowed_amount = 0
            term = 1 if self.need_short_term_loan() else self.term

            # 2.2. Ask for loan

            total_score = []
            for bank in banks:
                score = fl.total_score(weight=TOTAL_SCORE_WEIGHT, score=[self.relation_score[bank], self.size_score[bank]])
                total_score.append({bank: score})
                self.total_score[bank] = score

            bank_priority = sorted(total_score) # [{bank: 0.5}, ...] desc

            for bank_score in bank_priority:
                bank = bank_score.keys()[0]
                if bank.is_available_for_lendings():
                    if bank.can_give_a_loan_to(self):
                        real_borrowing_amount, scheduling_repayment = self.ask_for_a_loan(
                            bank, self.borrowing_target_amount - borrowed_amount, term)
                        if real_borrowing_amount > 0:
                            self.borrow(bank, real_borrowing_amount, scheduling_repayment)
                            bank.lend(self, real_borrowing_amount)
                            borrowed_amount += real_borrowing_amount
                            if self.borrowing_target_amount - borrowed_amount == 0:
                                break

            # relation_score
            for bank in banks:
                self.relation_score[bank] = fl.relation_score(self.relation_score[bank], borrowed_amount)

        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_2"

    def stage_3(self, banks):
        '''
        At stage 3, banks update other entries of the balance sheet
        '''
        self.update_equity()

        for bank in banks:
            if self.borrowings.get(bank, 0) > 0:
                amount = self.scheduled_repayment_amount[bank].pop(0)
                if self.cash < amount:
                    self.bankrupt()
                    break
                self.pay(bank, amount)
                bank.receive(self, amount)

        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_3"

    # ===================================================================

    def is_available(self):
        return self.bankrupted

    def is_available_for_lendings(self):
        return max(self.lending_target_amount * self.lending_target_rate - self.total_lendings(), 0) > 0

    def can_give_a_loan_to(self, bank):
        probability = fl.lending_decision(self.total_score[bank])
        return True if np.random.choice(2, 1, p=[1 - probability, probability])[0] == 1 else False

    def update_short_term_lending_rate(self):
        self.short_term_lending_rate = self.short_term_lending_rate

    def update_short_term_borrowing_rate(self):
        self.short_term_borrowing_rate = self.short_term_borrowing_rate

    def ask_for_a_loan(self, bank, borrow_amount_target, term):
        available_amount = bank.available_lending_amount()
        offer_amount = min(borrow_amount_target, available_amount)
        scheduling_repayment = [offer_amount / term for _ in range(term)] if offer_amount > 0 else []
        return offer_amount, scheduling_repayment

    def init_scheduled_payment(self, term):
        scheduled_repayment_amount = {}
        for bank_code in self.borrowings:
            total_borrowing_amount = self.borrowings[bank_code]
            short_term_payment_amount = self.short_term_borrowing_rate * total_borrowing_amount
            long_term_payment_amount = (1 - self.short_term_borrowing_rate) * total_borrowing_amount
            scheduled_repayment_amount[bank_code] = [0] + [short_term_payment_amount + float(long_term_payment_amount) / term] + [float(long_term_payment_amount) / term] * (term - 1)

    def need_a_loan(self):
        return True if np.random.uniform(0, 1) < 0 else False

    def need_short_term_loan(self):
        return True if np.random.uniform(0, 1) < 0 else False

    def update_borrowing_target_amount(self):
        self.borrowing_target_amount = max(self.borrowing_target_rate / (1 - self.borrowing_target_rate) * (self.deposit + self.equity) - self.total_borrowings(), 0)

    def update_lending_target_amount(self):
        self.lending_target_amount = max(self.total_asset() * self.borrowing_target_rate - self.total_lendings(), 0)

    def available_lending_amount(self):
        return self.lending_target_amount * self.lending_target_rate

    def other_agents(self, banks):
        return [bank for bank in banks if (self.unique_id != bank.unique_id) and (bank.is_available())]

    def update_scheduled_payment(self, bank, scheduled_payment):
        _ = [len(self.scheduled_repayment_amount[bank]), len(scheduled_payment)]
        add_term = max(_) - min(_)
        if (len(self.scheduled_repayment_amount[bank]) != len(scheduled_payment)):
            if len(self.scheduled_repayment_amount[bank]) > len(scheduled_payment):
                scheduled_payment += [0 for _ in range(add_term)]
            else:
                self.scheduled_repayment_amount[bank] += [0 for _ in range(add_term)]

        self.scheduled_repayment_amount[bank] = [x + y for x, y in zip(self.scheduled_repayment_amount[bank], scheduled_payment)]

    def deposit_growth_rate(self):
        return np.random.normal(self.growth_rate["deposit"]["mean"], self.growth_rate["deposit"]["var"])

    def external_asset_growth_rate(self):
        return np.random.normal(self.growth_rate["external_asset"]["mean"], self.growth_rate["external_asset"]["var"])

    def equity_growth_rate(self):
        return np.random.normal(self.growth_rate["equity"]["mean"], self.growth_rate["equity"]["var"])