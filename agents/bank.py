import numpy as np

from mesa import Agent
import model.fomulas as fl
import math
from data.contanst import *

class Bank(Agent):
    def __init__(self, params):
        self.code = params.get("code", "")
        self.name = self.code
        self.unique_id = self.code

        self.term = LOAN_TERM

        # Liabilities
        liability = params.get("liability", {})
        self.equity = liability.get("equity", 0)
        self.deposit = liability.get("deposit", 0)
        # self.total_borrowings() == liability["total"] - self.equity - self.deposit
        borrowings = params.get("borrowings", {})
        self.borrowings = {code: borrowings[code] for code in borrowings if code != self.code}

        # Assets
        asset = params.get("asset", {})
        self.external_asset = asset.get("external_asset", 0) + asset.get("cash", 0)
        # self.total_lendings() == asset["total"] - self.external_asset
        lendings = params.get("lendings", {})
        self.lendings = {code: lendings[code] for code in lendings if code != self.code}

        self.short_term_lending_rate = params.get("short_term_lending_rate", 0)
        self.short_term_borrowing_rate = params.get("short_term_borrowing_rate", 0)

        self.scheduled_repayment_amount = {}
        self.init_scheduled_payment(self.term)

        self.growth_rate = params.get("growth_rate", {"deposit":        {"mean": 0, "var": 0},
                                                      "external_asset": {"mean": 0, "var": 0},
                                                      "equity":         {"mean": 0, "var": 0}})

        self.external_asset_target_rate = params.get("external_asset_target_rate", 0.7)
        self.borrowing_target_rate = params.get("borrowing_target_rate", 0)
        self.lending_target_rate = params.get("lending_target_rate", 0)
        self.deposit_target_rate = params.get("deposit_target_rate", 0.6)

        self.recover_rate_params = params.get("recover_rate", {"min": 0, "max": 0})

        self.is_a_large_bank = params.get("large_bank", False)

        self.relation_indicators = {bank_code: 1 if self.lendings[bank_code] > 0 else 0 for bank_code in self.lendings}
        # ======

        self.total_asset_target_amount = 0
        self.borrowing_target_amount = 0
        self.lending_target_amount = 0
        # self.deposit_target_amount = 0
        self.borrowing_amount = 0
        self.lending_amount = 0
        self.lending_count = 0
        self.ask_amount = 0

        self.bankrupted = False

        self.bankrupting_processor = params.get("bankrupting_processor", None)
        self.is_affected_by_bankrupting = False

        self.is_shocked = False
        self.bankrupted_equity = 0
        self.bankrupted_asset = 0
        self.available_lending_target_amount = 0

    def step(self, stage, banks):
        """ A single step of the agent. """
        if stage in [1, 2, 3]:
            return {
                1: self.stage_1,
                2: self.stage_2,
                3: self.stage_3,
                4: self.stage_4,
            }[stage](banks)

    # ===================================================================

    def total_borrowings(self):
        return sum(self.borrowings.values())

    def total_lendings(self):
        return sum(self.lendings.values())

    def total_asset(self):
        return self.total_lendings() + self.external_asset

    def total_liability(self):
        return self.deposit + self.total_borrowings() + self.equity

    def check_balance_sheet_problem(self):
        return round(self.total_asset() - self.total_liability(), 5) == 0

    # ===================================================================

    def pay(self, bank, amount):
        print "--->", 'Code:', str(self.code), "- Name:", self.name, ":", "paid", amount
        self.external_asset -= amount
        self.borrowings[bank.code] -= amount


    def receive(self, bank, amount):
        print "--->", 'Code:', str(self.code), "- Name:", self.name, ":", "received", amount
        self.external_asset += amount
        self.lendings[bank.code] -= amount


    def lend(self, bank, amount):
        print "--->", 'Code:', str(self.code), "- Name:", self.name, ":", "lend", amount
        self.external_asset -= amount
        self.lendings[bank.code] += amount

    def borrow(self, bank, amount, scheduled_payment):
        print "--->", 'Code:', str(self.code), "- Name:", self.name, ":", "borrowed", amount
        self.external_asset += amount
        self.borrowings[bank.code] += amount
        self.ask_amount -= amount
        self.update_scheduled_payment(bank, scheduled_payment)

    # ===================================================================

    def update_deposit(self):
        print "--->", 'Code:', str(self.code), "deposit", ":", self.deposit, "-", "external asset:", self.external_asset
        new_deposit = self.deposit * math.exp(self.deposit_growth_rate())
        self.external_asset += new_deposit - self.deposit
        self.deposit = new_deposit
        print "updated_deposit", "-", "deposit", ":", self.deposit, "-", "external asset:", self.external_asset

    def update_equity(self):
        print "--->", 'Code:', str(self.code), "equity:", self.equity, "-", "external asset:", self.external_asset
        new_equity = self.equity * (1 + self.equity_growth_rate())
        self.external_asset += new_equity - self.equity
        self.equity = new_equity
        print "--->" "updated_equity", "-", "new_equity", ":", self.equity, "-", "external asset:", self.external_asset

    # ===================================================================

    def bankrupting(self, banks):
        self.bankrupted = True
        recover_rate = self.recover_rate()
        other_banks = self.other_agents(banks)

        self.is_affected_by_bankrupting = True
        self.sell_asset(other_banks, recover_rate)

        total_debt = self.deposit + self.total_borrowings()
        print 'total borrowing', self.total_borrowings()
        print 'borrowing', self.borrowings
        print 'deposit', self.deposit
        print 'total debt', total_debt
        print 'external asset', self.external_asset
        print
        if total_debt > 0:
            print "external asset before repayment deposit (bankrupted):", self.external_asset
            external_asset = self.external_asset
            self.external_asset -= external_asset * self.deposit / total_debt if total_debt > 0 else 0
            self.deposit = 0

            for bank in banks:
                if not bank.bankrupted and self.borrowings[bank.code] > 0:
                    print "external asset before repayment bank", bank.code, "(bankrupted):", self.external_asset
                    repay = external_asset * self.borrowings[bank.code] / total_debt
                    loss_amount = self.borrowings[bank.code] - repay

                    self.pay(bank, repay)
                    bank.receive(self, repay)

                    bank.equity -= loss_amount
                    bank.bankrupted_equity += loss_amount
                    bank.bankrupted_asset += loss_amount

                    bank.is_affected_by_bankrupting = True
                    self.scheduled_repayment_amount[bank.code] = []
                    self.borrowings[bank.code] = bank.lendings[self.code] = 0

    # ===================================================================

    def stage_1(self, banks):
        '''
        A model step. At stage 1, borrowing banks repay part of their loan to lending banks
        '''
        self.update_deposit()
        self.update_total_asset_target_amount()
        self.update_lending_target_amount()
        self.update_borrowing_target_amount()

        print 'Code:', str(self.code), 'Balance Sheet', ":", str(self.check_balance_sheet_problem())
        print 'Code:', str(self.code), "- Name:", self.name, "--> Run", "stage_1"

    def stage_2(self, banks):
        '''
        At stage 2, banks borrow and lend in the interbank market
        '''
        print 'Code:', str(self.code), "- Name:", self.name, "--> Run", "stage_2"

        term = 1 if self.need_short_term_loan() else self.term

        # 2.2. Ask for loan

        self.ask_amount = self.borrowing_target_amount
        for bank in banks:
            if self.ask_amount > 0:
                bank.limit = bank.available_lending_target_amount / 5
                if not bank.is_bankrupted() and bank.is_available_for_lendings():
                    if bank.can_give_a_loan_to(self):
                        real_borrowing_amount = round(min(self.ask_amount, bank.available_lending_amount(), bank.limit), 5)
                        print 'Real borrowing amount =', real_borrowing_amount
                        print '---> Code', self.code, 'lending', '- amount:', real_borrowing_amount,\
                            "- remaining amount:", self.ask_amount - real_borrowing_amount, \
                            'Bank:', bank.code, \
                            "- available amount:", bank.available_lending_amount()
                        scheduling_repayment = [real_borrowing_amount / term] * term if real_borrowing_amount > 0 else []
                        self.borrow(bank, real_borrowing_amount, scheduling_repayment)
                        bank.lend(self, real_borrowing_amount)

        print 'Code:', str(self.code), 'Balance Sheet', ":", str(self.check_balance_sheet_problem())


    def stage_3(self, banks):
        '''
        At stage 3, banks update other entries of the balance sheet
        '''
        self.update_equity()

        for bank in banks:
            if self.borrowings.get(bank.code, 0) > 0 and len(self.scheduled_repayment_amount[bank.code]) > 0:
                repay_amount = self.scheduled_repayment_amount[bank.code].pop(0)
                self.pay(bank, repay_amount)
                bank.receive(self, repay_amount)

        print 'Code:', str(self.code), 'Balance Sheet', ":", str(self.check_balance_sheet_problem()), \
            'diff = ', math.fabs(self.total_asset() - self.total_liability())
        print 'Code:', str(self.code), "- Name:", self.name, "--> Run", "stage_3"

    def stage_4(self, banks):
        pass

    # ===================================================================
    # Helper Function used for all process
    def is_available(self):
        return not self.bankrupted

    def other_agents(self, banks):
        return [bank for bank in banks if (self.unique_id != bank.unique_id)]

    ## Functions related to bankrupt
    def is_bankrupted(self):
        if self.bankrupted:
            return True
        # In case equity < 0
        if self.total_asset() < self.deposit + self.total_borrowings():
            return True
        return False

    ### Bankrupting process Function
    def recover_rate(self):
        return np.random.uniform(self.recover_rate_params["min"], self.recover_rate_params["max"])

    def sell_asset(self, banks, recover_rate):
        new_external_asset = self.external_asset * recover_rate
        self.bankrupted_asset += self.external_asset - new_external_asset
        self.external_asset = new_external_asset
        print 'Code', self.code, 'sell debt:'
        for bank in banks:
            if not bank.bankrupted and self.lendings[bank.code] > 0:
                debt = recover_rate * self.lendings[bank.code]

                print '---> Code', bank.code, 'bought debt', "-", \
                    "external_asset", ":", bank.external_asset, "-", "debt", ":", debt

                bank.is_affected_by_bankrupting = True

                repay_debt = min(bank.external_asset, debt)
                bank.pay(self, repay_debt)
                self.receive(bank, repay_debt)

                loss_amount = self.lendings[bank.code] - repay_debt
                bank.equity += loss_amount
                self.bankrupted_asset += loss_amount

                bank.borrowings[self.code] = self.lendings[bank.code] = 0
                bank.scheduled_repayment_amount[self.code] = []

    # ===================================================================
    # # Stage 1 Helper function

    ## 1.2. Update target of total asset (compare to EA), update deposit, lending, borrowing as fixed ratio compared with total asset
    def update_total_asset_target_amount(self):
        self.total_asset_target_amount = self.deposit / self.deposit_target_rate
        print "--->", 'Code:', str(self.code), "total asset target:", self.total_asset_target_amount

    def update_borrowing_target_amount(self):
        old_borrowing_target_amount = self.borrowing_target_amount
        self.borrowing_target_amount = self.total_asset_target_amount * self.borrowing_target_rate
        self.borrowing_target_amount = max(self.borrowing_target_amount - self.total_borrowings(), 0)
        print "--->", 'Code:', str(self.code), "borrowing_target:", old_borrowing_target_amount, \
            "and new_borrowing_target:", self.borrowing_target_amount

    def update_lending_target_amount(self):
        self.lending_target_amount = self.total_asset_target_amount * self.lending_target_rate
        self.available_lending_target_amount = self.available_lending_amount()
        print "--->", 'Code:', str(self.code), "lending:", self.lending_target_amount, "and available lending:", \
            self.available_lending_target_amount

    def available_lending_amount(self):
        return max(self.lending_target_amount - self.total_lendings(), 0)

    ## 1.3. Update deposit (Deposit update function above)
    def deposit_growth_rate(self):
        deposit_growth_rate = np.random.normal(self.growth_rate["deposit"]["mean"], self.growth_rate["deposit"]["var"])
        print "--->", 'Code:', str(self.code), "deposit growth rate", deposit_growth_rate
        return deposit_growth_rate

    # ===================================================================
    # Stage 2 Helper function
    ## 2.1. Ask for a loan

    ## 2.2. helper function for lending decision
    def is_available_for_lendings(self):
        return self.available_lending_amount() > 0

    def can_give_a_loan_to(self, bank):
        run_out_of_debt = self.lendings[bank.code] == 0 and self.borrowings[bank.code] == 0

        if self.is_a_large_bank:
            probability = np.random.uniform(0.2, 0.8) if run_out_of_debt else np.random.uniform(0.6, 1)
        else:
            probability = np.random.uniform(0, 0.7) if run_out_of_debt else np.random.uniform(0.4, 0.9)

        print 'Offer loan probability = ', probability
        return True if np.random.choice(2, 1, p=[1 - probability, probability])[0] == 1 else False


    # Functions related termed payments (use in stage 2 + stage 3)
    def init_scheduled_payment(self, term):
        self.scheduled_repayment_amount = {}
        for bank_code in self.borrowings:
            total_borrowing_amount = self.borrowings[bank_code]
            short_term_payment_amount = self.short_term_borrowing_rate * total_borrowing_amount
            long_term_payment_amount = (1 - self.short_term_borrowing_rate) * total_borrowing_amount
            self.scheduled_repayment_amount[bank_code] = [0] + [short_term_payment_amount + float(long_term_payment_amount) / term] + [float(long_term_payment_amount) / term] * (term - 1)

    def need_short_term_loan(self):
        return True if np.random.uniform(0, 1) < 0.5 else False

    def update_scheduled_payment(self, bank, scheduled_payment):
        _ = [len(self.scheduled_repayment_amount[bank.code]), len(scheduled_payment)]
        add_term = max(_) - min(_)
        if len(self.scheduled_repayment_amount[bank.code]) != len(scheduled_payment):
            if len(self.scheduled_repayment_amount[bank.code]) > len(scheduled_payment):
                scheduled_payment += [0 for _ in range(add_term)]
            else:
                self.scheduled_repayment_amount[bank.code] += [0 for _ in range(add_term)]

        self.scheduled_repayment_amount[bank.code] = [x + y for x, y in zip(self.scheduled_repayment_amount[bank.code], scheduled_payment)]

    # ===================================================================
    # Stage 3 Helper function
    def equity_growth_rate(self):
        return np.random.normal(self.growth_rate["equity"]["mean"], self.growth_rate["equity"]["var"])

    def round_scheduled_repayment_amount(self):
        return {bank_code: [round(_, 5) \
                            for _ in self.scheduled_repayment_amount[bank_code]]\
                for bank_code in self.scheduled_repayment_amount}

    def set_shock(self, be_shocked=True):
        self.is_shocked = be_shocked

    def get_shock_rate(self):
        return 0.2

    def shocked(self):
        self.is_shocked = False
        loss_amount = self.external_asset * self.get_shock_rate()
        self.external_asset -= loss_amount
        self.bankrupted_asset += loss_amount
        self.bankrupted_equity += min(self.equity, loss_amount)
        self.equity = max(self.equity - loss_amount, 0)
