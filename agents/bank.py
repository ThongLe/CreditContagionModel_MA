import numpy as np

from mesa import Agent
import model.fomulas as fl

class Bank(Agent):
    def __init__(self, params):
        self.code = params['code'] if 'code' in params else ''
        self.name = params['name'] if 'name' in params else ''
        self.unique_id = self.name + "(" + str(self.code) + ")"

    def step(self, stage, banks):
        """ A single step of the agent. """
        if stage in [1, 2, 3]:
            return {
                1: self.stage_1,
                2: self.stage_2,
                3: self.stage_3
            }[stage](banks)

    def pay(self, amount):
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "paid" + " " + str(amount)

    def receive(self, amount):
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "received" + " " + str(amount)

    def lend(self, amount):
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "lend" + " " + str(amount)

    def borrow(self, amount):
        print "---> " + 'Code: ' + str(self.code) + " - Name: " + self.name + " : " + "borrowed" + " " + str(amount)

    def change_deposit(self):
        print "change_deposit"

    def change_external_asset(self):
        print "change_external_asset"

    def change_equity(self):
        print "change_equity"

    def bankrupt(self):
        print "bankrupt"

    def stage_1(self, banks):
        '''
        A model step. At stage 1, borrowing banks repay part of their loan to lending banks
        '''

        for bank in banks:
            if bank.code != self.code:
                amount = fl.repay_amount(s=0, b=0)
                self.pay(amount)
                bank.receive(amount)

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