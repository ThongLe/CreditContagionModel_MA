import numpy as np

from mesa import Agent
import model.fomulas as fl
from data.banks import SHORT_TERM_DEBT_RATIO

class Bank(Agent):
    def __init__(self, params):
        self.code = params.get("code", "")
        self.name = params.get("name", "")
        self.unique_id = self.name + "(" + str(self.code) + ")"

        self.short_term_debt = params.get("short_term_debt", {})
        self.debts = params.get("debts", {})
        self.cash = params.get("cash", 0)
        self.loans = params.get("loans", {})
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

    def long_term_debt(self):
        return {bank_code: self.debts[bank_code] - self.short_term_debt[bank_code] for bank_code in self.debts.keys()}

    def total_debt(self):
        return sum(self.debts.values())

    def total_loan(self):
        return sum(self.loans.values())

    def pay(self, bank, amount):
        self.cash -= amount
        self.short_term_debt[bank.code] -= amount
        self.debts[bank.code] -= amount
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "paid" + " " + str(amount)

    def receive(self, bank, amount):
        self.cash += amount
        self.loans[bank.code] -= amount
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "received" + " " + str(amount)

    def lend(self, bank, amount):
        self.cash -= amount
        self.loans[bank.code] += amount
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "lend" + " " + str(amount)

    def borrow(self, bank, amount):
        self.cash += amount
        self.short_term_debt[bank.code] += amount
        self.debts[bank.code] += amount
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
            if (bank.code != self.code) and (self.short_term_debt[bank.code] > 0):
                amount = fl.repay_amount(s=SHORT_TERM_DEBT_RATIO, b=self.short_term_debt[bank.code])
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