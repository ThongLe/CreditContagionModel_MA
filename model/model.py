import random
import copy

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

from agents.bank import Bank
from agents.bankrupting_processor import BankruptingProcessor

from data.banks_1 import params, lending_borrowing_matrix_1
from schedule import RandomActivationByBreed

import csv
import os

class CreditContagionModel(Model):

    initial_bank = 100

    ### To do
    def __init__(self, shock_type='Type_1', shocked_bank_number=1, initial_bank=20, stable_count_limit=10, \
                 test_case=0, shock_rate=0):
        self.name = "Credit Contagion Model"

        # Set parameters
        self.initial_bank = initial_bank
        self.verbose = True

        self.schedule = RandomActivationByBreed(self)

        self.data_collector = self.create_data_collector()

        bankrupting_processor = BankruptingProcessor()
        self.shocked_bank_number = shocked_bank_number
        agents = []
        for i in range(self.initial_bank):
            params[i]["lendings"] = lending_borrowing_matrix_1[params[i]["code"]]
            params[i]["borrowings"] = { bank: lending_borrowing_matrix_1[bank][params[i]["code"]] for bank in lending_borrowing_matrix_1 }
            params[i]["bankrupting_processor"] = bankrupting_processor
            agent = Bank(params[i], shock_rate)
            agents.append(agent)
            self.schedule.add(agent)

        bankrupting_processor.set_context({"banks": agents})
        self.schedule.add(bankrupting_processor)

        self.shock_type = shock_type
        self.stable_count_limit = stable_count_limit
        self.test_case = test_case
        self.shock_rate = shock_rate

    def step(self, i_step, shock=False):
        self.set_shocked_bank(self.shocked_bank_number) if shock else None
        self.data_collector.collect(self)
        self.export_interbank_matrix(i_step)
        self.process_shock() if shock else None

        stages = [1, 2, 3, 4]
        for stage in stages:
            self.schedule.step(stage, cycle_stage=stages.__len__())

        if self.verbose:
            print([self.schedule.time,
                   self.schedule.get_breed_count(Bank)])

    def run_model(self, limit_step=1, stable_count_limit=10):
        self.stable_count_limit = self.stable_count_limit or stable_count_limit
        if self.verbose:
            print('Project Name: ' + self.name)
            print('Initial number banks: ',
                  self.schedule.get_breed_count(Bank))

        step, i, stable_count, bankrupted_bank_count = 0, 0, 0, 0
        while step < limit_step or stable_count < self.stable_count_limit:
            self.schedule.set_run_time(step + i)
            count = self.initial_bank - self.schedule.number_bankrupted_bank()
            if bankrupted_bank_count != count:
                stable_count = 0
                bankrupted_bank_count = count
            else:
                stable_count += 1

            step, i = (step + 1, i) if step <= limit_step else (step, i + 1)
            if step == limit_step:
                self.step(step + i, True)
            else:
                self.step(step + i)

    def create_data_collector(self):
        model_reporters = {
            "Type_Test": lambda m: "Type 1",
            "Step": lambda m: m.schedule.get_run_time(),
            "Banks": lambda m: m.schedule.get_breed_count(Bank),
            "Total_Asset": lambda m: m.schedule.total_assets(),
            "Total_Equity": lambda m: m.schedule.total_equity(),
            "Number_Of_Live_Banks": lambda m: m.schedule.number_live_bank(),
            "Number_Of_Bankrupted_Banks": lambda m: m.schedule.number_bankrupted_bank(),
            "Number_Of_Affected_Banks": lambda m: m.schedule.number_affected_bank(),
            "Total_Bankrupted_Asset": lambda m: m.schedule.total_bankrupted_asset(),
            "Total_Bankrupted_Equity": lambda m: m.schedule.total_bankrupted_equity()
        }
        agent_reporters = {
            "equity": lambda bank: round(bank.equity, 5),
            "deposit": lambda bank: round(bank.deposit, 5),
            "external_asset": lambda bank: str(round(bank.external_asset, 5)) + ('(shocked)' if bank.is_shocked else ""),
            "scheduled_repayment_amount": lambda bank: copy.deepcopy(bank.round_scheduled_repayment_amount()),
            "lendings": lambda bank: copy.deepcopy({_: round(bank.lendings[_], 5) for _ in bank.lendings}),
            "borrowings": lambda bank: copy.deepcopy({_: round(bank.lendings[_], 5) for _ in bank.borrowings}),
            "is_bankrupted": lambda bank: str(bank.bankrupted) + ('(' + str(bank.bankrupted_id) + ')') if bank.bankrupted else '',
            "bankrupted_asset": lambda bank: bank.bankrupted_asset,
            "bankrupted_equity": lambda bank: bank.bankrupted_equity
        }
        return DataCollector(model_reporters, agent_reporters)

    def export_report(self):
        self.export_agent_vars()
        self.export_model_vars()

    def export_agent_vars(self):
        report_types = self.data_collector.agent_vars.keys()
        for report_type in report_types:
            report = self.data_collector.agent_vars[report_type]
            with open(self.build_file_path(report_type), 'wb') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=',')
                bank_name = [report[0][i][0] for i in range(0, self.initial_bank)]
                spamwriter.writerow(bank_name)
                for row in report:
                    values = [row[i][1] for i in range(0, self.initial_bank)]
                    spamwriter.writerow(values)

    def export_model_vars(self):
        with open(self.build_file_path('overview_report'), 'wb') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            keys = self.data_collector.model_vars.keys()
            spamwriter.writerow(keys)
            if keys.__len__() > 0:
                for i in range(0, self.data_collector.model_vars[keys[0]].__len__()):
                    values = [self.data_collector.model_vars[key][i] for key in keys]
                    spamwriter.writerow(values)

    def export_interbank_matrix(self, step):
        interbank_matrix = self.schedule.interbank_matrix()
        with open(self.build_file_path('interbank_matrix_' + str(step)), 'wb') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            for interbank_row in interbank_matrix:
                spamwriter.writerow(interbank_row)

    def build_file_path(self, report_type):
        file_path = 'statistic_reports/' + self.shock_type + '/shock_rate_' + str(self.shock_rate) + '/' + \
                    str(self.test_case) + '/' + report_type + '.csv'
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        return file_path

    def set_shocked_bank(self, number_of_banks):
        shock_count = 0
        banks = self.schedule.agents_by_breed[Bank]
        while shock_count < number_of_banks:
            bank_index = random.randint(0, self.initial_bank - 1)
            if not banks[bank_index].is_shocked:
                shock_count += 1
                banks[bank_index].set_shock()

    def process_shock(self):
        banks = self.schedule.agents_by_breed[Bank]
        for bank in banks:
            bank.shocked() if bank.is_shocked else None