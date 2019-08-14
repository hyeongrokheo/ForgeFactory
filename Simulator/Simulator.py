from Equipment.Cutter import *
from Equipment.Press import *
from Equipment.TreatmentFurnace import *
from Planner.HeuristicAllocator import *
from Planner.GAAllocator import *

class Simulator:
    def __init__(self, type, predictor, product, ingot, job, heating_furnace_num, press_num, cutter_num, treatment_furnace_num):

        self.type = type
        # 'Heuristic', 'GA'

        #original data
        self.original_product = product
        self.original_ingot = ingot
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
        self.treatment_furnace_list = None

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
        self.product = deepcopy(self.original_product)
        self.ingot = deepcopy(self.original_ingot)
        self.job = deepcopy(self.original_job)

        self.heating_furnace_list = []
        self.press_list = []
        self.cutter_list = []
        self.treatment_furnace_list = []

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
        if self.type == 'Heuristic':
            self.alloc = HeuristicAllocator(self.env, self.predictor, self.heating_furnace_num, self.job)
        elif self.type == 'GA':
            self.alloc = GAAllocator(self.env, self.predictor, self.heating_furnace_num, self.job)
        else:
            print('Error : Simulator type is not valid.', self.type)
            exit(1)

        for i in range(self.heating_furnace_num):
            self.heating_furnace_list.append(HeatingFurnace(self.env, self.alloc, i))
        for i in range(self.press_num):
            self.press_list.append(Press(self.env, self.alloc, i))
        for i in range(self.cutter_num):
            self.cutter_list.append(Cutter(self.env, self.alloc, i))
        for i in range(self.treatment_furnace_num):
            self.treatment_furnace_list.append(TreatmentFurnace(self.env, self.alloc, i))

    def get_logs(self):
        logs = {'heating_furnace': [], 'press': [], 'cutter': [], 'treatment_furnace': []}
        for hf in self.heating_furnace_list:
            logs['heating_furnace'].append(deepcopy(hf.log))
        for p in self.press_list:
            logs['press'].append(deepcopy(p.log))
        for c in self.cutter_list:
            logs['cutter'].append(deepcopy(c.log))
        for tf in self.treatment_furnace_list:
            logs['treatment_furnace'].append(deepcopy(tf.log))
        #print('p.log :', logs['press'][0])
        return logs

    def set_job_queue(self, individual):
        self.alloc.set_job_queue(individual)

    def set_envs(self, envs):
        #print('Log :', envs['heating_furnace'][0])
        self.start_time = envs['time']
        allocator_data = envs['allocator']
        self.alloc.set_env(self.start_time, allocator_data)
        heating_furnace_logs = envs['heating_furnace']
        for i in range(len(self.heating_furnace_list)):
            self.heating_furnace_list[i].set_env(self.start_time, heating_furnace_logs[i])
        press_logs = envs['press']
        for i in range(len(self.press_list)):
            self.press_list[i].set_env(self.start_time, press_logs[i])
        cutter_logs = envs['cutter']
        for i in range(len(self.cutter_list)):
            self.cutter_list[i].set_env(self.start_time, cutter_logs[i])
        treatment_furnace_logs = envs['treatment_furnace']
        for i in range(len(self.treatment_furnace_list)):
            self.treatment_furnace_list[i].set_env(self.start_time, treatment_furnace_logs[i])

    def run(self, simulate_time, save_env = False):
        if Debug_mode:
            print('- running simulator -')
        #print(self.equips)
        for hf in self.heating_furnace_list:
            self.env.process(hf.run())
            self.env.process(hf.recharging())
            self.env.process(hf.discharging())
        for p in self.press_list:
            self.env.process(p.run())
        for c in self.cutter_list:
            self.env.process(c.run())
        for tf in self.treatment_furnace_list:
            self.env.process(tf.run())
        self.env.process(self.alloc._recharging())

        if save_env:
            simul_end_time = 60 * 22 #22시간 후
            self.env.run(until=simul_end_time)
            self.envs = {'time': self.env.now, 'jobs': deepcopy(self.job), 'allocator': {}, 'heating_furnace': [], 'press': [], 'cutter': [], 'treatment_furnace': []}
            self.envs['allocator']['waiting_job'] = deepcopy(self.alloc.waiting_job)
            self.envs['allocator']['complete_job'] = deepcopy(self.alloc.complete_job)
            self.envs['allocator']['recharging_queue'] = deepcopy(self.alloc.recharging_queue)
            for hf in self.heating_furnace_list:
                self.envs['heating_furnace'].append(deepcopy(hf.log))
            for p in self.press_list:
                self.envs['press'].append(deepcopy(p.log))
            for c in self.cutter_list:
                self.envs['cutter'].append(deepcopy(c.log))
            for tf in self.treatment_furnace_list:
                self.envs['treatment_furnace'].append(deepcopy(tf.log))

        simul_end_time = 60 * 24 * simulate_time # N일 후
        self.env.run(until=simul_end_time)
        #self.env.run(until=60*24*14)
        if save_env:
            self.envs2 = {'time': self.env.now, 'jobs': deepcopy(self.job), 'allocator': {}, 'heating_furnace': [],
                         'press': [], 'cutter': [], 'treatment_furnace': []}
            self.envs2['allocator']['waiting_job'] = deepcopy(self.alloc.waiting_job)
            self.envs2['allocator']['complete_job'] = deepcopy(self.alloc.complete_job)
            self.envs2['allocator']['recharging_queue'] = deepcopy(self.alloc.recharging_queue)
            for hf in self.heating_furnace_list:
                self.envs2['heating_furnace'].append(deepcopy(hf.log))
            for p in self.press_list:
                self.envs2['press'].append(deepcopy(p.log))
            for c in self.cutter_list:
                self.envs2['cutter'].append(deepcopy(c.log))
            for tf in self.treatment_furnace_list:
                self.envs2['treatment_furnace'].append(deepcopy(tf.log))

        if Debug_mode:
            print('- end simulator -')
        #for j in self.job:
            #if j['properties']['state'] != 'done':
                #print('Error : 미완료된 작업 존재')
                #print(j)
                #exit(1)
        energy = 0
        for hf in self.heating_furnace_list:
            energy += hf.total_energy_usage
        for p in self.press_list:
            energy += p.total_energy_usage
        for c in self.cutter_list:
            energy += c.total_energy_usage
        for tf in self.treatment_furnace_list:
            energy += tf.total_energy_usage
        simulation_time = simul_end_time
        total_weight = 3000
        total_heating_weight = 0
        for hf in self.heating_furnace_list:
            total_heating_weight += hf.total_heating_weight

        return energy, simulation_time, total_weight, total_heating_weight

    """def __init__(self, heating_furnaces_num):
        self.heating_furnaces_num = heating_furnaces_num
        self.environment = simpy.Environment()
        self.allocator = Allocator(self.environment)
        #environment.process(allocator.allocate())

        heating_furnace = HeatingFurnace(self.environment, self.allocator, 1)
        self.environment.process(heating_furnace.run())
        heating_furnace2 = HeatingFurnace(self.environment, self.allocator, 2)
        self.environment.process(heating_furnace2.run())

        heating_furnaces = []
        #print(self.heating_furnaces_num)
        #for i in range(self.heating_furnaces_num):
        #    print(i)
        #    heating_furnaces.append(HeatingFurnace(self.environment, self.allocator, i))
        #    self.environment.process(heating_furnaces[i].run())
        #print('aa')

        #for i in range(self.heating_furnaces_num):
        #    self.environment.process(heating_furnaces[i].run())

    def run(self):
        self.environment.run()
    """