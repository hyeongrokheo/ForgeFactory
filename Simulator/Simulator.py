from Equipment.Cutter import *
from Equipment.Press import *
from Equipment.TreatmentFurnace import *
from Planner.HeuristicAllocator import *

class Simulator:
    def __init__(self, predictor, job, heating_furnace_num, press_num, cutter_num, treatment_furnace_num):


        #original data
        # self.original_product = product
        # self.original_ingot = ingot
        self.original_job = job

        self.product = None
        self.ingot = None
        self.job = None

        self.heating_furnace_num = heating_furnace_num
        self.press_num = press_num
        self.cutter_num = cutter_num
        self.treatment_furnace_num = treatment_furnace_num

        self.env = None
        self.predictor = predictor
        self.alloc = None

        self.heating_furnace_list = None
        self.press_list = None
        self.cutter_list = None
        self.treatment_furnace = None

        # self.init_envs = None
        self.envs = None
        self.envs2 = None
        self.start_time = None
        # self.heating_furnace_logs = None
        # self.press = None
        # self.cutter_logs = None
        # self.treatment_furnace_logs = None

        self.init_simulator()

    def init_simulator(self):
        if Debug_mode:
            print('- simulator initialize -')
        # self.product = deepcopy(self.original_product)
        # self.ingot = deepcopy(self.original_ingot)
        self.job = deepcopy(self.original_job)

        self.heating_furnace_list = []
        self.press_list = []
        self.cutter_list = []
        self.treatment_furnace = None

        self.envs = None
        self.envs2 = None
        self.start_time = None
        # if equips != None:
        #     self.env = equips['env']
        #     self.alloc = equips['alloc']
        #     for i in range(self.heating_furnace_num):
        #         self.heating_furnace_list.append(equips['heating_furnace'][i])
        #     for i in range(self.press_num):
        #         self.press_list.append(equips['press'][i])
        #     for i in range(self.cutter_num):
        #         self.cutter_list.append(equips['cutter'][i])
        #     for i in range(self.treatment_furnace_num):
        #         self.treatment_furnace_list.append(equips['treatment_furnace'][i])
        # else:
        self.env = simpy.Environment()
        self.alloc = HeuristicAllocator(self.env, self.predictor, self.heating_furnace_num, self.job)

        for i in range(self.heating_furnace_num):
            self.heating_furnace_list.append(HeatingFurnace(self.env, self.alloc, i))
        for i in range(self.press_num):
            self.press_list.append(Press(self.env, self.alloc, i))
        for i in range(self.cutter_num):
            self.cutter_list.append(Cutter(self.env, self.alloc, i))
        self.treatment_furnace = TreatmentFurnace(self.env, self.alloc)

    def re_init_simulator(self):
        self.treatment_furnace = TreatmentFurnace(self.env, self.alloc)

    def get_logs(self):
        logs = {'heating_furnace': [], 'press': [], 'cutter': [], 'treatment_furnace': []}
        for hf in self.heating_furnace_list:
            logs['heating_furnace'].append(deepcopy(hf.log))
        for p in self.press_list:
            logs['press'].append(deepcopy(p.log))
        for c in self.cutter_list:
            logs['cutter'].append(deepcopy(c.log))
        return logs

    def set_job_queue(self, individual):
        self.alloc.set_job_queue(individual)

    def run(self, simulate_time):
        if Debug_mode:
            print('- running simulator -')
        for hf in self.heating_furnace_list:
            self.env.process(hf.run())
            self.env.process(hf.recharging())
            self.env.process(hf.discharging())
        for p in self.press_list:
            self.env.process(p.run())
        for c in self.cutter_list:
            self.env.process(c.run())
        self.env.process(self.treatment_furnace.run())
        self.env.process(self.alloc._recharging())

        simul_end_time = 60 * 24 * simulate_time # N일 후
        self.env.run(until=simul_end_time)

        energy = 0
        for hf in self.heating_furnace_list:
            energy += hf.total_energy_usage
        for p in self.press_list:
            energy += p.total_energy_usage
        for c in self.cutter_list:
            energy += c.total_energy_usage
        simulation_time = simul_end_time
        total_weight = 3000
        total_heating_weight = 0
        for hf in self.heating_furnace_list:
            total_heating_weight += hf.total_heating_weight

        # treatment_job_list = deepcopy(self.treatment_furnace.treatment_job_list)
        treatment_job_list = self.treatment_furnace.treatment_job_list
        return energy, simulation_time, total_weight, total_heating_weight, treatment_job_list