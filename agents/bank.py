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
        self.cash = asset.get("cash", 0)
        self.external_asset = asset.get("external_asset", 0)
        # self.total_lendings() == asset["total"] - self.cash - self.external_asset
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
        self.deposit_target_amount = 0
        self.borrowing_amount = 0
        self.lending_amount = 0
        self.lending_count = 0
        self.ask_amount = 0

        self.bankrupted = False

        self.relation_score = {}
        self.size_score = {}
        self.total_score = {}

        self.bankrupting_processor = params.get("bankrupting_processor", None)
        self.is_affected_by_bankrupting = False

        self.is_shocked = False

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
        return self.cash + self.total_lendings() + self.external_asset

    def total_liability(self):
        return self.deposit + self.total_borrowings() + self.equity

    def check_balance_sheet_problem(self):
        return round(self.total_asset() - self.total_liability(), 5) == 0

    # ===================================================================

    def pay(self, bank, amount):
        print "--->", 'Code:', str(self.code), "- Name:", self.name, ":", "paid", amount
        self.cash -= amount
        self.borrowings[bank.code] -= amount


    def receive(self, bank, amount):
        print "--->", 'Code:', str(self.code), "- Name:", self.name, ":", "received", amount
        self.cash += amount
        self.lendings[bank.code] -= amount


    def lend(self, bank, amount):
        print "--->", 'Code:', str(self.code), "- Name:", self.name, ":", "lend", amount
        self.cash -= amount
        self.lendings[bank.code] += amount

    def borrow(self, bank, amount, scheduled_payment):
        print "--->", 'Code:', str(self.code), "- Name:", self.name, ":", "borrowed", amount
        self.cash += amount
        self.borrowings[bank.code] += amount
        self.update_scheduled_payment(bank, scheduled_payment)

    # ===================================================================

    def update_deposit(self):
        noise_rate = self.deposit_noise_rate()
        new_deposit = self.deposit_target_amount * (1 + noise_rate)
        print "--->", 'Code:', str(self.code), "updated_deposit", "-", "deposit_target_amount", ":", \
            self.deposit_target_amount, "-", "new_deposit", ":", new_deposit, '-', 'noise rate :', noise_rate
        self.cash += new_deposit - self.deposit
        self.deposit = new_deposit

    def update_external_asset(self):
        if self.is_shocked:
            shock_rate = self.get_shock_rate()
            new_external_asset = self.external_asset * (1 - shock_rate)
            self.equity -= self.external_asset * shock_rate

            print "--->(SHOCK)", 'Code:', str(self.code), "updated_external_asset", "-", "external_asset", ":", \
                self.external_asset, "- shock_rate :", shock_rate, "-", "new_external_asset", ":", new_external_asset
        else:
            external_asset_growth_rate = self.external_asset_growth_rate()
            new_external_asset = self.external_asset * math.exp(external_asset_growth_rate)
            self.cash -= new_external_asset - self.external_asset

            print "--->", 'Code:', str(self.code), "updated_external_asset", "-", "external_asset", ":", \
                self.external_asset, "- growth_rate:", external_asset_growth_rate, "-", "new_external_asset", ":", new_external_asset

        self.external_asset = new_external_asset

    def update_equity(self):
        equity_growth_rate = self.equity_growth_rate()
        new_equity = self.equity * (1 + equity_growth_rate)
        print "--->", 'Code:', str(self.code), "updated_equity", "-", "equity", ":", self.equity, "-", \
            "growth_rate: ", equity_growth_rate, "-", "new_equity", ":", new_equity
        self.cash += new_equity - self.equity
        self.equity = new_equity

    def update_cash(self):
        self.cash = self.total_liability() - self.total_lendings() - self.external_asset

    # ===================================================================

    def bankrupting(self, banks):
        recover_rate = self.recover_rate()
        other_banks = self.other_agents(banks)
        self.sell_asset(other_banks, recover_rate)

        total_debt = self.deposit + self.total_borrowings()
        if total_debt > 0:
            total_cash = self.cash

            self.cash -= total_cash * self.deposit / total_debt if total_debt > 0 else 0
            self.deposit = 0

            for bank in banks:
                if self.borrowings[bank.code] > 0:
                    repay = total_cash * self.borrowings[bank.code] / total_debt
                    self.pay(bank, repay)
                    self.borrowings[bank.code] = 0
                    bank.equity -= self.borrowings[bank.code] - repay
                    self.scheduled_repayment_amount[bank.code] = []
                    bank.receive(self, repay)
                    bank.lendings[self.code] = 0

        print "--->", 'Code:', str(self.code), "bankrupted", "-", "cash", ":", self.cash

    # ===================================================================

    def stage_1(self, banks):
        '''
        A model step. At stage 1, borrowing banks repay part of their loan to lending banks
        '''
        self.update_external_asset()
        self.update_total_asset_target_amount()
        self.update_lending_target_amount()
        self.update_deposit_target_amount()
        self.update_borrowing_target_amount()
        self.update_deposit()
        self.update_cash()

        print "--->", 'Code:', str(self.code), '- cash :', self.cash

        # if self.is_bankrupted():
        #     self.bankrupting(banks)

        print 'Code:', str(self.code), 'Balance Sheet', ":", str(self.check_balance_sheet_problem())
        print 'Code:', str(self.code), "- Name:", self.name, "--> Run", "stage_1"

    def stage_2(self, banks):
        '''
        At stage 2, banks borrow and lend in the interbank market
        '''
        banks = self.update_size_score(banks)
        self.update_total_score(banks)

        borrowed_amount = 0
        term = 1 if self.need_short_term_loan() else self.term

        # 2.2. Ask for loan

        total_score = [{bank: self.total_score[bank]} for bank in banks]
        bank_priority = sorted(total_score) # [{bank: 0.5}, ...] desc
        self.ask_amount = self.borrowing_target_amount

        for bank_score in bank_priority:
            bank = bank_score.keys()[0]
            print '---> Code', self.code, 'total_score with Bank', bank.code, ":", bank_score.values()[0]
            bank.available_lending_amount = bank.lending_target_amount
            bank.limit = bank.lending_target_amount / 5
            if not bank.is_bankrupted() and bank.is_available_for_lendings():
                if bank.can_give_a_loan_to(self):
                    real_borrowing_amount = round(min(self.ask_amount, bank.available_lending_amount, bank.limit), 5)
                    print '---> Code', self.code, 'lending', '- amount:', real_borrowing_amount,\
                        "- remaining amount:", self.ask_amount - real_borrowing_amount, \
                        'Bank:', bank.code, \
                        "- available amount:", bank.available_lending_amount - real_borrowing_amount
                    self.ask_amount -= real_borrowing_amount
                    bank.available_lending_amount -= real_borrowing_amount
                    if real_borrowing_amount > 0:
                        scheduling_repayment = [real_borrowing_amount / term for _ in range(term)]\
                            if real_borrowing_amount > 0 else []
                        self.borrow(bank, real_borrowing_amount, scheduling_repayment)
                        bank.lend(self, real_borrowing_amount)
                        borrowed_amount += real_borrowing_amount
                        if self.borrowing_amount - borrowed_amount == 0:
                            break

        self.update_relation_score(banks, borrowed_amount)

        print "--->", 'Code:', str(self.code), '- cash :', self.cash

        if self.is_bankrupted():
            self.bankrupting(banks)

        print 'Code:', str(self.code), 'Balance Sheet', ":", str(self.check_balance_sheet_problem())
        print 'Code:', str(self.code), "- Name:", self.name, "--> Run", "stage_2"

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

        print 'Code:', str(self.code), 'Balance Sheet', ":", str(self.check_balance_sheet_problem()),\
            'diff = ', math.fabs(self.total_asset() - self.total_liability())
        print 'Code:', str(self.code), "- Name:", self.name, "--> Run", "stage_3"

    def stage_4(self, banks):
        pass

    # ===================================================================
    # Helper Function used for all process
    def is_available(self):
        return not self.bankrupted

    def other_agents(self, banks):
        return [bank for bank in banks if (self.unique_id != bank.unique_id)] # and (bank.is_available())]

    ## Functions related to bankrupt
    def is_bankrupted(self):
        if self.bankrupted:
            return True
        # In case equity < 0
        if self.total_asset() < self.deposit + self.total_borrowings():
            self.bankrupted = True
            return True
        # In case cash < 0
        if self.total_liability() < self.external_asset + self.total_lendings():
            self.bankrupted = True
            return True

        return False

    ### Bankrupting process Function
    def recover_rate(self):
        return np.random.uniform(self.recover_rate_params["min"], self.recover_rate_params["max"])

    def sell_external_asset(self):
        cash = self.external_asset
        self.external_asset = 0
        return cash

    def sell_asset(self, banks, recover_rate):
        cash = recover_rate * self.sell_external_asset()
        self.cash += cash
        print 'Code', self.code, 'sell debt:'
        for bank in banks:
            if not bank.is_bankrupted() and self.lendings[bank.code] > 0:
                debt = recover_rate * self.lendings[bank.code]
                if bank.cash < debt:
                    # bank.bankrupted = True
                    print '---> Code', bank.code, 'has not enough cash', "-", "cash", ":", bank.cash, "-", "debt", ":", debt
                    self.bankrupting_processor.add_bank(bank)
                else:
                    print '---> Code', bank.code, 'bought debt', "-", "cash", ":", bank.cash, "-", "debt", ":", debt
                repay_debt = min(bank.cash, debt)
                bank.cash -= repay_debt
                self.cash += repay_debt
                self.cash = round(self.cash, 5)
                bank.borrowings[self.code] = self.lendings[bank.code] = 0
                bank.scheduled_repayment_amount[self.code] = []

    # ===================================================================
    # Stage 1 Helper function
    ##1.1. Set growth rate of EA => Update EA (function to update above)
    def external_asset_growth_rate(self):
        return np.random.normal(self.growth_rate["external_asset"]["mean"], self.growth_rate["external_asset"]["var"])

    ## 1.2. Update target of total asset (compare to EA), update deposit, lending, borrowing as fixed ratio compared with total asset

    def update_total_asset_target_amount(self):
        self.total_asset_target_amount = self.external_asset / self.external_asset_target_rate
        print '---> Code', self.code, 'update_total_asset_target_amount :', self.total_asset_target_amount, "=", \
            "external_asset(" + str(self.external_asset) + ")/ external_asset_target_rate(" + \
            str(self.external_asset_target_rate) + ")"

    def update_borrowing_target_amount(self):
        self.borrowing_target_amount = self.total_asset_target_amount * self.borrowing_target_rate
        self.borrowing_target_amount = max(self.borrowing_target_amount - self.total_borrowings(), 0)
        print '---> Code', self.code, 'update_borrowing_target_amount:', self.borrowing_target_amount, "-", \
            "total_asset_target_amount(" + str(self.total_asset_target_amount) + ") * borrowing_target_rate(" + \
            str(self.borrowing_target_rate) + ")", "-", "total_borrowings() :", self.total_borrowings()

    def update_lending_target_amount(self):
        self.lending_target_amount = self.total_asset_target_amount * self.lending_target_rate
        self.available_lending_amount = max(self.lending_target_amount - self.total_lendings(), 0)
        print '---> Code', self.code, 'update_lending_target_amount:', self.lending_target_amount, "-", \
            "total_asset_target_amount(" + str(self.total_asset_target_amount) + ") * lending_target_rate(" + \
            str(self.lending_target_rate) + ")", "-", "total_lendings() :", self.total_lendings()


    def update_deposit_target_amount(self):
        self.deposit_target_amount = self.total_asset_target_amount * self.deposit_target_rate
        print '---> Code', self.code, 'update_deposit_target_amount:', self.deposit_target_amount, "-", \
            "total_asset_target_amount(" + str(self.total_asset_target_amount) + ") * deposit_target_rate(" + \
            str(self.deposit_target_rate) + ")"


            ## 1.3. Update deposit (Deposit update function above)
    def deposit_noise_rate(self):
        # return np.random.standard_normal(1)[0]
        return np.random.uniform(-0.02, 0.02)

    # ===================================================================
    # Stage 2 Helper function
    ## 2.1. Ask for a loan

    ## 2.2. helper function for lending decision
    def is_available_for_lendings(self):
        return max(self.lending_target_amount * self.lending_target_rate - self.total_lendings(), 0) > 0

    def init_scores(self, banks):
        self.update_relation_score(banks)
        self.update_size_score(banks)
        self.update_total_score(banks)

    def update_relation_score(self, banks, borrowed_amount=None):
        if borrowed_amount is None:
            self.relation_score = {bank: fl.relation_score(0, self.total_borrowings()) for bank in banks}
        else:
            self.relation_score = {bank: fl.relation_score(self.relation_score[bank], borrowed_amount) for bank in
                                   banks}

    def update_size_score(self, banks):
        bank_assets, indicators, live_banks = [], [], []
        for bank in banks:
            if round(bank.total_asset(), 0) > 0:
                live_banks.append(bank)
                total_asset = max(bank.total_asset(), 0)
                bank_assets.append(total_asset)
                indicators.append(self.relation_indicators[bank.code])
        tmp = {bank: fl.size_score(bank.total_asset(), bank_assets, indicators) for bank in live_banks}
        self.size_score = {}
        if len(live_banks) > 0:
            max_score = max(np.abs(tmp.values()))
            if max != 0:
                self.size_score = {bank: 5 * tmp[bank] / max_score for bank in tmp}
            else:
                self.size_score = {bank: 0 for bank in tmp}
        for bank in self.size_score:
            if float(str(self.size_score[bank])) == float('Inf'):
                a = 0
        return live_banks

    def update_total_score(self, banks):
        for bank in banks:
            if bank in self.size_score:
                score = fl.total_score(weight=TOTAL_SCORE_WEIGHT, score=[self.relation_score[bank], self.size_score[bank]])
                if float(str(score)) == float('Inf') or float(str(score)) == float('nan'):
                    a = 0
                self.total_score[bank] = score

    def alpha(self):
        if self.is_a_large_bank:
            return np.random.uniform(0.3, 0.5)
        return np.random.uniform(0.9, 1.1)

    def beta(self):
        return np.random.uniform(-1.1, -0.9)

    def can_give_a_loan_to(self, bank):
        probability = fl.lending_decision(self.total_score[bank], self.alpha(), self.beta())
        try:
            return True if np.random.choice(2, 1, p=[1 - probability, probability])[0] == 1 else False
        except:
            return False

    # Functions related termed payments (use in stage 2 + stage 3)
    def update_short_term_lending_rate(self):
        self.short_term_lending_rate = self.short_term_lending_rate

    def update_short_term_borrowing_rate(self):
        self.short_term_borrowing_rate = self.short_term_borrowing_rate

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
        self.is_shocked = False
        return 0.5