import random

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

from agents.bank import Bank
from agents.bankrupting_processor import BankruptingProcessor

from data.banks import params, lending_borrowing_matrix
from schedule import RandomActivationByBreed

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
            "Banks": lambda m: m.schedule.get_breed_count(Bank)
        }
        agent_reporters = {
            "Test": lambda bank: 0
        }
        return DataCollector(model_reporters, agent_reporters)