from VirtualFactory.V_Cutter import *
from VirtualFactory.V_Press import *
from VirtualFactory.V_TreatmentFurnace import *
from VirtualFactory.V_Allocator import *
from VirtualFactory.V_HeatingFurnace import *
import simpy

class V_Simulator:
    def __init__(self, predictor, product, ingot, job, heating_furnace_num, press_num, cutter_num, treatment_furnace_num):
        self.product = product
        self.ingot = ingot
        self.job = job

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

        self.envs = None

        self.init_simulator()

    def init_simulator(self):
        if Debug_mode:
            print('- simulator initialize -')

        self.heating_furnace_list = []
        self.press_list = []
        self.cutter_list = []
        self.treatment_furnace_list = []

        self.env = simpy.Environment()
        self.alloc = V_Allocator(self.env, self.predictor, self.heating_furnace_num, self.job)

        for i in range(self.heating_furnace_num):
            self.heating_furnace_list.append(V_HeatingFurnace(self.env, self.alloc, i))
        for i in range(self.press_num):
            self.press_list.append(V_Press(self.env, self.alloc, i))
        for i in range(self.cutter_num):
            self.cutter_list.append(V_Cutter(self.env, self.alloc, i))
        for i in range(self.treatment_furnace_num):
            self.treatment_furnace_list.append(V_TreatmentFurnace(self.env, self.alloc, i))

    def set_envs(self, envs):
        self.start_time = envs['time']
        #allocator_data = envs['allocator']
        #self.alloc.set_env(self.start_time, allocator_data)
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

    def set_todo(self, log):
        #print(log)
        for i in range(len(self.heating_furnace_list)):
            self.heating_furnace_list[i].set_todo(log['heating_furnace'][i])
        for i in range(len(self.press_list)):
            self.press_list[i].set_todo(log['press'][i])
        for i in range(len(self.cutter_list)):
            self.cutter_list[i].set_todo(log['cutter'][i])
        for i in range(len(self.treatment_furnace_list)):
            self.treatment_furnace_list[i].set_todo(log['treatment_furnace'][i])

    def run(self, simulation_time):
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
        #self.env.process(self.alloc._recharging())

        simul_end_time = 60 * 24  * simulation_time - 120 #22시간 후
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
        #self.envs['time'] = self.env.now
        #self.envs['hf'] = []
        #for i in range(len(self.heating_furnace_list)):
        #    self.envs['hf'].append(self.heating_furnace_list[i].get_data())

        simul_end_time = 60 * 24  * simulation_time #24시간 후
        self.env.run(until=simul_end_time)

        if Debug_mode:
            print('- end simulator -')
        #for j in self.job:
            #if j['properties']['state'] != 'done':
                #print('Error : 미완료된 작업 존재')
                #print(j)
                #exit(1)
        energy = random.randint(1000, 2000)
        #T = random.randint(1000, 2000)
        simulation_time = self.alloc.simulate_end_time
        total_weight = random.randint(1000, 2000)
        total_heating_weight = random.randint(1000, 2000)
        total_e = random.randint(1000, 2000)

        return energy, simulation_time, total_weight, total_heating_weight
