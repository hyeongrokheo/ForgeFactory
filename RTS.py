# from Simulator.ForgeSimulator import ForgeSimulator

import array
import random
import time
from copy import deepcopy
from UtilFunction import *

from deap import base
from deap import creator
from deap import tools



class RTS:
    # popsize=100, ngen=500
    def __init__(self, simulator, envs, popsize=100, ngen=9000, w1=10.0, w2=1.0):
        # job_id_list : 작업 계획 대상 작업 전체 (3000톤)
        self.simulator = simulator
        #self.entity_mgr = copy.deepcopy(simulator.entity_mgr)
        self.envs = envs
        self.job_list = self.envs['jobs']
        self.total_weight = self.get_total_weight()
        self.furnace_id_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        #self.total_weight_chk = {}
        # for furnace in self.entity_mgr.get('heating_furnace'):
        #     self.total_weight_chk[furnace.id] = furnace.properties['capacity']
        #     self.furnace_id_list.append(furnace.id)
        self.furnace_list = [x for x in range(len(self.furnace_id_list))]
        self.popsize = int(popsize)
        self.ngen = int(ngen)
        self.w1 = w1
        self.w2 = w2
        self.cnt = 0

    # def set_env(self, envs):
    #     self.envs = envs


    def getDistance(self, ind1, ind2):
        sum = 0
        for i in range(len(ind1)):
            if ind1[i] != ind2[i]:
                sum += 1
        return sum

    def findMostSimilarInd(self, pool, ind):
        most_similar = 0
        best_distance = self.getDistance(pool[0], ind)
        count = len(pool)
        for i in range(1, count):
            cur_distance = self.getDistance(pool[i], ind)
            if (cur_distance < best_distance):
                most_similar = i
                best_distance = cur_distance
        return pool[most_similar]

    def evaluate(self, individual):
        start_t = time.time()
        if Debug_mode:
            print('individual :', individual)

        #self.simulator.init_entity_manager()
        #furnace_schedule = self.decoder(individual, self.simulator.entity_mgr)
        self.simulator.init_simulator()
        self.simulator.set_envs(self.envs)
        self.simulator.set_job_queue(deepcopy(individual))
        #시뮬레이터에 인자로 individual 넣어주고 하면 됨

        energy, simulation_time, total_weight, total_heating_weight = self.simulator.run()
        W = random.randint(2900, 3100)
        #W = self.total_weight - self.simulator.total_weight()
        if total_weight == 0:
            total_weight = self.total_weight
        #E_modify = E * (self.total_weight / W)
        #T_modify = T * (self.total_weight / W)

        energy_per_ton = energy/total_weight
        E_modify = energy / W
        time_per_ton = simulation_time / W
        if simulation_time == 0:
            print('Error : T is',simulation_time)
            simulation_time = 1
        heating_ton_per_time = total_heating_weight/simulation_time * 3600
        # if heating_ton_per_time == 0:
        #     score = energy_per_ton * 2 + 100 * 50
        # else:
        #     score = energy_per_ton * 2 + (1/heating_ton_per_time) * 50

        score = (E_modify * self.w1) + (time_per_ton * self.w2)
        self.cnt += 1
        print('simulation', self.cnt)
        print('score : ', '{0:.3f}'.format(score), end='\t')
        print('time (minute) ', '{0:.3f}'.format(simulation_time), end='\t')
        print('energy : ', '{0:.3f}'.format(energy), end='\t')
        print('weight :', '{0:.3f}'.format(total_weight), end='\t')
        print('energy per ton: ', '{0:.3f}'.format(energy_per_ton), end='\t')
        print('time per ton: ', '{0:.3f}'.format(time_per_ton), end='\t')
        print('heating per time: ', '{0:.3f}'.format(heating_ton_per_time), end='\t')
        print('total_heating_weight : ', '{0:.3f}'.format((total_weight - heating_ton_per_time)/simulation_time*3600), end='\t')
        print('total_heating_weight : ', '{0:.3f}'.format(total_heating_weight), end='\t')
        # print('Total heating energy ', self.simulator.heating_energy())
        # print('total ', total_e)
        total_dict = {}
        total_dict['heat_treating_furnace'] = 0
        total_dict['cutter'] = 0
        total_dict['press'] = 0

        total_dict['heating_furnace'] = {}
        fur_total = total_dict['heating_furnace']
        fur_total['heating'] = 0
        fur_total['door_manipulate'] = 0
        fur_total['reheating'] = 0
        fur_total['maintaining'] = 0

        name_list = ['heat_treating_furnace', 'heating_furnace', 'cutter', 'press']

        # for key, value in total_e.items():
        #     if name_list[0] in key:
        #         total_dict[name_list[0]] += float('{0:.3f}'.format(value['operate']))
        #     if name_list[2] in key:
        #         total_dict[name_list[2]] += float('{0:.3f}'.format(value['operate']))
        #     if name_list[3] in key:
        #         total_dict[name_list[3]] += float('{0:.3f}'.format(value['operate']))
        #     if name_list[1] in key:
        #         dictt = total_dict[name_list[1]]
        #         for k, e in value.items():
        #             if k in dictt:
        #                 total_dict[name_list[1]][k] += float('{0:.3f}'.format(e))
        #     # print(key, value)
        # print(total_dict)
        print('time is', time.time() - start_t)
        return score,

    def run(self):
        gen_length = len(self.job_list)
        self.cnt = 0
        mutation_indpb = float(1/gen_length)
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", array.array, typecode='i', fitness=creator.FitnessMin)

        toolbox = base.Toolbox()

        # Attribute generator
        toolbox.register("furnaces", random.choice, self.furnace_list)

        # Structure initializers
        toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.furnaces, n=gen_length)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mate", tools.cxUniform, indpb=0.2)
        toolbox.register("mutate", tools.mutUniformInt, low=0, up=12, indpb=mutation_indpb)

        # :param tournsize: The number of individuals participating in each tournament.
        toolbox.register("select", tools.selTournament, tournsize=10)
        toolbox.register("evaluate", self.evaluate)

        # 필요하면 쓰고, 아니면 지울 부분
        # stats = tools.Statistics(lambda ind: ind.fitness.values)
        # stats.register("avg", numpy.mean)
        # stats.register("std", numpy.std)
        # stats.register("min", numpy.min)
        # stats.register("max", numpy.max)

        ### RTS Algorithm ###

        # crossover parameter
        CXPB = 1
        # mutation parameter
        MUTPB = 1
        # RTS parameter
        MAT_POOL_SIZE = 2
        REP_POOL_SIZE = self.popsize

        population = toolbox.population(n=self.popsize)
        fits = toolbox.map(toolbox.evaluate, population)

        for fit, ind in zip(fits, population):
            ind.fitness.values = fit

        self.best_list = []
        best_so_far = None
        for pop in population:
            if best_so_far is None:
                best_so_far = pop
            else:
                if pop.fitness.values[0] < best_so_far.fitness.values[0]:
                    best_so_far = pop
        self.best_list.append(best_so_far.fitness.values[0])
        #print('best so far', best_so_far.fitness.values[0], best_so_far)

        for g in range(0, self.ngen, 2):
            # Select the next generation individuals
            parents = toolbox.select(population, MAT_POOL_SIZE)

            # Clone the selected individuals
            offsprings = [toolbox.clone(ind) for ind in parents]

            # Apply crossover on the offspring
            for child1, child2 in zip(offsprings[::2], offsprings[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            # Apply mutation on the offspring
            for mutant in offsprings:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Evaluate the individuals with an invalid fitness
            for ind in offsprings:
                ind.fitness.values = toolbox.evaluate(ind)

            # Restricted Tournament Selection
            for offspring in offsprings:
                replace_pool = toolbox.select(population, REP_POOL_SIZE)
                most_similar = self.findMostSimilarInd(replace_pool, offspring)
                if (offspring.fitness.values[0] < most_similar.fitness.values[0]):
                    population.remove(most_similar)
                    population.append(offspring)

            # Best So Far
            for pop in offsprings:
                if best_so_far is None:
                    best_so_far = pop
                else:
                    if pop.fitness.values[0] < best_so_far.fitness.values[0]:
                        best_so_far = pop
            self.best_list.append(best_so_far.fitness.values[0])
            #print('best so far', best_so_far.fitness.values[0], best_so_far)
        best = None
        for pop in population:
            if best is None:
                best = pop
            else:
                if pop.fitness.values[0] < best.fitness.values[0]:
                    best = pop
        #print('best_so_far_list ', self.best_list)
        return best

    def decoder(self, individual, entity_mgr):
        furnace_schedule = {}
        for i in range(len(individual)):
            job_id = self.job_id_list[i]
            job = entity_mgr.get(job_id)
            furnace_id = self.furnace_id_list[individual[i]]
            if furnace_id not in [*furnace_schedule]:
                furnace_schedule[furnace_id] = []
            furnace_schedule[furnace_id].append(job.id)

            # 기존에는 job과 product에 기록해두고 쓰는 방식이었는데,
            # furnace_schedule 을 allocator에게 넘겨주고 작업할당하도록 구현하면 될 듯
            # if 'heating_furnace_' in job.types[-1]:
            #     job.types[-1] = furnace_id + '_heating'
            # else:
            #     job.types.append(furnace_id + '_heating')
            # entity_mgr.update(job)
            # product_id_list = job.product_id_list()
            # for product_id in product_id_list:
            #     product = entity_mgr.get(product_id)
            #     product.properties['report'][0]['equipment_id'] = furnace_id
            #     product.properties['report'][0]['start_time'] = None
            #     product.properties['report'][0]['end_time'] = None
        return furnace_schedule

    def score(self):
        E = self.simulator.total_results()
        T = self.simulator.total_time()
        T = (T - self.simulator.start_time).total_seconds()
        score = E * self.w1 + T * self.w2
        return score

    def get_total_weight(self):
        total = 0
        for j in self.job_list:
            weight = j['properties']['ingot']['current_weight']
            #weight = job.get_initial_weight(self.entity_mgr)
            total += weight
        return total

if __name__ == "__main__":
    for i in range(5):
        print(tools.mutUniformInt([4, 1], 0, 4, 1))
    tools.mutFlipBit(array('i', [4, 1, 2, 1, 1, 0, 2, 0, 2, 1, 4, 1, 4, 0, 3, 4, 0, 3, 3]), 1)
