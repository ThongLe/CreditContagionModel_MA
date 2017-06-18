import random

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

from agents.bank import Bank
from agents.bankrupting_processor import BankruptingProcessor

from data.banks import params, lending_borrowing_matrix
from schedule import RandomActivationByBreed

import csv

class CreditContagionModel(Model):

    initial_bank = 100

    ### To do
    def __init__(self, initial_bank=100):
        self.name = "Credit Contagion Model"

        # Set parameters
        self.initial_bank = initial_bank
        self.verbose = True

        self.schedule = RandomActivationByBreed(self)

        self.data_collector = self.create_data_collector()

        bankrupting_processor = BankruptingProcessor()
        agents = []
        for i in range(self.initial_bank):
            params[i]["lendings"] = lending_borrowing_matrix[params[i]["code"]]
            params[i]["borrowings"] = { bank: lending_borrowing_matrix[bank][params[i]["code"]] for bank in lending_borrowing_matrix }
            params[i]["bankrupting_processor"] = bankrupting_processor
            agent = Bank(params[i])
            agents.append(agent)

        for agent in agents:
            other_agents = agent.other_agents(agents)
            agent.init_scores(other_agents)
            self.schedule.add(agent)

        bankrupting_processor.set_context({"banks": agents})
        self.schedule.add(bankrupting_processor)

    def step(self):
        stages = [1, 2, 3]
        for stage in stages:
            self.schedule.step(stage, cycle_stage=stages.__len__())
        self.data_collector.collect(self)
        if self.verbose:
            print([self.schedule.time,
                   self.schedule.get_breed_count(Bank)])

    def run_model(self, step_count=200):
        if self.verbose:
            print('Project Name: ' + self.name)
            print('Initial number banks: ',
                  self.schedule.get_breed_count(Bank))

        for i in range(step_count):
            self.step()

        if self.verbose:
            print('')
            print('Final number banks: ',
                  self.schedule.get_breed_count(Bank))

    def create_data_collector(self):
        model_reporters = {
            "Banks": lambda m: m.schedule.get_breed_count(Bank),
            "Total_Asset": lambda m: m.schedule.total_assets(),
            "Total_Equity": lambda m: m.schedule.total_equity(),
            "Number_Of_Live_Banks": lambda m: m.schedule.number_live_bank(),
            "Number_Of_Bankrupted_Banks": lambda m: m.schedule.number_bankrupted_bank(),
            "Number_Of_Affected_Banks": lambda m: m.schedule.number_affected_bank()
        }
        agent_reporters = {
            "cash": lambda bank: bank.cash,
            "equity": lambda bank: bank.equity,
            "deposit": lambda bank: bank.deposit,
            "external_asset": lambda bank: bank.external_asset,
            "scheduled_repayment_amount": lambda bank: bank.scheduled_repayment_amount,
            "lendings": lambda bank: bank.lendings,
            "borrowings": lambda bank: bank.borrowings
        }
        return DataCollector(model_reporters, agent_reporters)

    def export_report(self):
        self.export_agent_vars()
        self.export_model_vars()

    def export_agent_vars(self):
        report_types = self.data_collector.agent_vars.keys()
        for report_type in report_types:
            report = self.data_collector.agent_vars[report_type]
            with open('statistic_reports/reports/' + report_type + '.csv', 'wb') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=',')
                bank_name = [report[0][i][0] for i in range(0, self.initial_bank)]
                spamwriter.writerow(bank_name)
                for row in report:
                    values = [row[i][1] for i in range(0, self.initial_bank)]
                    spamwriter.writerow(values)

    def export_model_vars(self):
        with open('statistic_reports/model_report.csv', 'wb') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            keys = self.data_collector.model_vars.keys()
            spamwriter.writerow(keys)
            if keys.__len__() > 0:
                for i in range(0, self.data_collector.model_vars[keys[0]].__len__()):
                    values = [self.data_collector.model_vars[key][i] for key in keys]
                    spamwriter.writerow(values)
