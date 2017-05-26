import numpy as np

from mesa import Agent

class Bank(Agent):
    def __init__(self, params):
        self.code = params['code'] if 'code' in params else ''
        self.name = params['name'] if 'name' in params else ''

    def step(self):
        """ A single step of the agent. """
        self.stage_1()
        self.stage_2()
        self.stage_3()

    def pay(self):
        print "pay"

    def receive(self):
        print "receive"

    def lend(self):
        print "lend"

    def borrow(self):
        print "borrow"

    def change_deposit(self):
        print "change_deposit"

    def change_external_asset(self):
        print "change_external_asset"

    def change_equity(self):
        print "change_equity"

    def bankrupt(self):
        print "bankrupt"

    def stage_1(self):
        '''
        A model step. At stage 1, borrowing banks repay part of their loan to lending banks
        '''
        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_1"

    def stage_2(self):
        '''
        At stage 2, banks borrow and lend in the interbank market
        '''
        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_2"

    def stage_3(self):
        '''
        At stage 3, banks update other entries of the balance sheet
        '''
        print 'Code: ' + str(self.code) + " - Name: " + self.name + " --> Run " + "stage_3"