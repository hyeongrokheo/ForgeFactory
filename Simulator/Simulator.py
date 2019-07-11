from Equipment.Cutter import *
from Equipment.Press import *
from Equipment.TreatmentFurnace import *
from Planner.HeuristicAllocator import *

class Simulator:
    def __init__(self, predictor, product, ingot, job, heating_furnace_num, press_num, cutter_num, treatment_furnace_num):
        print('- create simulator -')
        self.env = simpy.Environment()
        self.predictor = predictor
        self.alloc = HeuristicAllocator(self.env, self.predictor, heating_furnace_num)


        self.product = product
        self.ingot = ingot
        self.job = job

        self.heating_furnace_list = []
        self.press_list = []
        self.cutter_list = []
        self.treatment_furnace_list = []

        for i in range(heating_furnace_num):
            self.heating_furnace_list.append(HeatingFurnace(self.env, self.alloc, i))
        for i in range(press_num):
            self.press_list.append(Press(self.env, self.alloc, i))
        for i in range(cutter_num):
            self.cutter_list.append(Cutter(self.env, self.alloc, i))
        for i in range(treatment_furnace_num):
            self.treatment_furnace_list.append(TreatmentFurnace(self.env, self.alloc, i))

        self.init_simulator()

    def init_simulator(self):
        print('- simulator initialize -')
        self.alloc.job = self.job

    def run(self):
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
        print('- end simulator -')
        print(self.job)

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