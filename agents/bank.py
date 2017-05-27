import numpy as np

from mesa import Agent
import model.fomulas as fl

class Bank(Agent):
    def __init__(self, params):
        self.code = params.get("code", "")
        self.name = params.get("name", "")
        self.unique_id = self.name + "(" + str(self.code) + ")"

        # Liabilities
        self.repayment_amount = params.get("repayment_amount", {})
        self.short_term_debt_ratio = params.get("short_term_debt_ratio", 0)
        self.borrowings = params.get("borrowings", {})
        self.equity = params.get("equity", 0)
        self.deposit = params.get("deposit", 0)

        # Assets
        self.cash = params.get("cash", 0)
        self.lendings = params.get("lendings", {})
        self.external_asset = params.get("external_asset", {})
        self.is_bankrupt = False

    def step(self, stage, banks):
        """ A single step of the agent. """
        if stage in [1, 2, 3]:
            return {
                1: self.stage_1,
                2: self.stage_2,
                3: self.stage_3
            }[stage](banks)

    def is_available(self):
        return self.is_bankrupt

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

    def update_short_term_debt_ratio(self):
        # To do
        self.short_term_debt_ratio = 0

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

    def borrow(self, bank, amount):
        self.cash += amount
        self.borrowings[bank.code] += amount
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

        for bank in banks:
            if (bank.code != self.code) and (self.borrowings[bank.code] > 0):
                amount = self.repayment_amount[bank.code].pop(0)
                if self.cash < amount:
                    self.bankrupt()
                    break
                self.pay(bank, amount)
                bank.receive(self, amount)

        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_1"

    def stage_2(self, banks):
        '''
        At stage 2, banks borrow and lend in the interbank market
        '''
        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_2"

    def stage_3(self, banks):
        '''
        At stage 3, banks update other entries of the balance sheet
        '''
        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_3"