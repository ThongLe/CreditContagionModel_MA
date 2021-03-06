import random
from collections import defaultdict

from mesa.time import RandomActivation
from agents.bank import Bank
from agents.bankrupting_processor import BankruptingProcessor
import operator

class RandomActivationByBreed(RandomActivation):
    '''
    A scheduler which activates each type of agent once per step, in random
    order, with the order reshuffled every step.

    This is equivalent to the NetLogo 'ask breed...' and is generally the
    default behavior for an ABM.

    Assumes that all agents have a step() method.
    '''
    agents_by_breed = defaultdict(list)

    def __init__(self, model):
        RandomActivation.__init__(self, model)
        self.agents_by_breed = defaultdict(list)
        self.run_time = 0

    def add(self, agent):
        '''
        Add an Agent object to the schedule

        Args:
            agent: An Agent to be added to the schedule.
        '''

        self.agents.append(agent)
        agent_class = agent.__class__
        self.agents_by_breed[agent_class].append(agent)

    def remove(self, agent):
        '''
        Remove all instances of a given agent from the schedule.
        '''

        while agent in self.agents:
            self.agents.remove(agent)

        agent_class = type(agent)
        while agent in self.agents_by_breed[agent_class]:
            self.agents_by_breed[agent_class].remove(agent)

    def step(self, stage, cycle_stage):
        '''
        Executes the step of each agent breed, one at a time, in random order.
        '''
        self.step_bank(stage)
        self.step_bankrupting()

        if stage % cycle_stage == 0:
            self.steps += 1
            self.time += 1

    def step_bank(self, stage):
        '''
        Shuffle order and run all agents of a given breed.

        Args:
            breed: Class object of the breed to run.
        '''
        banks = self.agents_by_breed[Bank]
        bankrupting_processor = self.agents_by_breed[BankruptingProcessor][0]
        random.shuffle(banks)
        for bank in banks:
            if not bank.is_bankrupted():
                bank.step(stage, bank.other_agents(banks))
            else:
                bankrupting_processor.add_bank(bank)

    def step_bankrupting(self):
        bankrupting_processor = self.agents_by_breed[BankruptingProcessor][0]
        bankrupting_processor.processing()

    def get_breed_count(self, breed_class):
        '''
        Returns the current number of agents of certain breed in the queue.
        '''
        return len(self.agents_by_breed[breed_class])

    def total_assets(self):
        banks = self.agents_by_breed[Bank]
        return sum([bank.total_asset() for bank in banks])

    def total_equity(self):
        banks = self.agents_by_breed[Bank]
        return sum([bank.equity for bank in banks])

    def number_live_bank(self):
        banks = self.agents_by_breed[Bank]
        return len([bank for bank in banks if not bank.is_bankrupted()])

    def number_bankrupted_bank(self):
        banks = self.agents_by_breed[Bank]
        return len([bank for bank in banks if bank.is_bankrupted()])

    def number_affected_bank(self):
        banks = self.agents_by_breed[Bank]
        return len([bank for bank in banks if bank.is_affected_by_bankrupting])

    def set_run_time(self, time):
        self.run_time = time

    def get_run_time(self):
        return self.run_time

    def interbank_matrix(self):
        banks = self.agents_by_breed[Bank]
        banks = sorted(banks, key=operator.attrgetter('code'))
        mtx = [[""] + [bank.code for bank in banks]]
        for bank in banks:
            mtx += [[bank.code] + [bank.borrowings.get(_.code, 0) for _ in banks]]
        return mtx