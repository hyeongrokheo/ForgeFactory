from Equipment.Cutter import *
from Equipment.Press import *
from Equipment.TreatmentFurnace import *
from Planner.HeuristicAllocator import *
from Planner.GAAllocator import *

class Simulator:
    def __init__(self, predictor, product, ingot, job, heating_furnace_num, press_num, cutter_num, treatment_furnace_num):
        print('- create simulator -')
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

        #self.init_simulator()

    def init_simulator(self, individual):
        if Debug_mode:
            print('- simulator initialize -')
        self.product = deepcopy(self.original_product)
        self.ingot = deepcopy(self.original_ingot)
        self.job = deepcopy(self.original_job)

        self.env = simpy.Environment()
        #self.alloc = HeuristicAllocator(self.env, self.predictor, self.heating_furnace_num, self.job)
        self.alloc = GAAllocator(self.env, self.predictor, self.heating_furnace_num, self.job, individual)

        self.heating_furnace_list = []
        self.press_list = []
        self.cutter_list = []
        self.treatment_furnace_list = []

        for i in range(self.heating_furnace_num):
            self.heating_furnace_list.append(HeatingFurnace(self.env, self.alloc, i))
        for i in range(self.press_num):
            self.press_list.append(Press(self.env, self.alloc, i))
        for i in range(self.cutter_num):
            self.cutter_list.append(Cutter(self.env, self.alloc, i))
        for i in range(self.treatment_furnace_num):
            self.treatment_furnace_list.append(TreatmentFurnace(self.env, self.alloc, i))

    def run(self):
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
        for tf in self.treatment_furnace_list:
            self.env.process(tf.run())
        self.env.process(self.alloc._recharging())

        simul_end_time = 60 * 24 * 30 #n일 후
        self.env.run(until=simul_end_time)
        if Debug_mode:
            print('- end simulator -')
        for j in self.job:
            if j['properties']['state'] != 'done':
                print('Error : 미완료된 작업 존재')
                print(j)
                exit(1)
        energy = random.randint(1000, 2000)
        #T = random.randint(1000, 2000)
        simulation_time = self.alloc.simulate_end_time
        total_weight = random.randint(1000, 2000)
        total_heating_weight = random.randint(1000, 2000)
        total_e = random.randint(1000, 2000)

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