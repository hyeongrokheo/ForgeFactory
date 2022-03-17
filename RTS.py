# from Simulator.ForgeSimulator import ForgeSimulator

import array
import random
import time
from copy import deepcopy
from UtilFunction import *

from deap import base
from deap import creator
from deap import tools
# import matplotlib.pyplot as plt

def createIndividual(job_length, preheat_length, tempering_length):
    ind = []
    for i in range(job_length):
        ind.append(i)
    random.shuffle(ind)
    # update1227 : 예열, 템퍼링 gene 범위 0 ~ 6 (열처리로 개수) (완)
    for i in range(preheat_length + tempering_length):
        ind.append(random.randrange(0, 7))
    return ind

def multiCrossover(ind1, ind2, job_length, preheat_length, tempering_length, indpb):
    ind1_1 = ind1[0:job_length]
    ind1_2 = ind1[job_length : job_length + preheat_length + tempering_length]
    ind2_1 = ind2[0:job_length]
    ind2_2 = ind2[job_length : job_length + preheat_length + tempering_length]
    if len(ind1) == 0 or len(ind2) == 0:
        return ind1, ind2

    ind1_1, ind2_1 = tools.cxPartialyMatched(ind1_1, ind2_1)
    # print('ind1 :', ind1_1, ind1_2)
    # print('ind2 :', ind2_1, ind2_2)

    ind1_2, ind2_2 = tools.cxUniform(ind1_2, ind2_2, indpb)

    ind1 = ind1_1 + ind1_2
    ind2 = ind2_1 + ind2_2

    return ind1, ind2

def mutMultiFrom(ind, job_length, preheat_length, tempering_length, indpb):
    ind_1 = ind[0:job_length]
    ind_2 = ind[job_length : job_length + preheat_length + tempering_length]

    ind_1 = tools.mutShuffleIndexes(ind_1, indpb)
    ind_2 = tools.mutUniformInt(ind_2, 0, 7, indpb)

    ind = ind_1+ind_2

    return ind

class RTS:
    # popsize=100, ngen=500
    def __init__(self, simulator, last_env, treatment_job_list, popsize=100, ngen=8900, w1=10.0, w2=1.0):
        # job_id_list : 작업 계획 대상 작업 전체 (3000톤)
        self.simulator = simulator
        self.last_env = last_env
        self.job_list = treatment_job_list
        self.total_weight = self.get_total_weight()
        self.furnace_id_list = [0, 1, 2, 3, 4, 5, 6, 7]
        self.furnace_list = [x for x in range(len(self.furnace_id_list))]
        self.popsize = int(popsize)
        self.ngen = int(ngen)
        self.w1 = w1
        self.w2 = w2
        self.cnt = 0
        self.best_log = None
        self.best_score = 0
        self.job_length = None
        self.preheat_length = None
        self.tempering_length = None
        self.day = None

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

    def evaluate(self, ori_individual):
        individual = deepcopy(ori_individual)
        self.cnt += 1
        print('simulation', self.cnt, ':')
        # print('individual :', len(individual), individual)
        self.simulator.init_simulator()
        self.simulator.re_init_simulator(self.job_list, individual, self.job_length, self.preheat_length, self.tempering_length, last_env=deepcopy(self.last_env))
        # print('job len :', len(self.job_list))
        energy, total_treatment_weight, penalty_count, logs, last_env = self.simulator.run(7, day=self.day)
        # penalty_count = self.simulator.alloc.penalty_count
        if energy == 0:
            energy = 100000000
        if total_treatment_weight == 0:
            total_treatment_weight = 1
        ton_per_energy = total_treatment_weight/energy
        # E_modify = energy / total_weight
        # if simulation_time == 0:
        #     print('Error : T is',simulation_time)
        #     simulation_time = 1
        # heating_ton_per_hour = total_heating_weight/simulation_time

        # 수정필요
        # score = energy_per_ton * self.w1 + total_treatment_weight * self.w2 수정필요
        # print('penalty :', penalty_count)
        print('ton per energy :', ton_per_energy)
        print('total treatment weight :', total_treatment_weight)
        # print('weight :', self.w1, self.w2)
        # score *= -1
        self.w1 = 100000
        self.w2 = 1
        self.w3 = 100
        score = ton_per_energy * self.w1 + total_treatment_weight * self.w2 - penalty_count * self.w3

        if self.best_score < score:
            self.best_score = score
            # self.best_log = self.simulator.get_logs()
            # print('best log :', self.best_log['press'][0])


        print('score :', '{0:.3f}'.format(score))
        # print('{0:.3f}'.format(score))

        if self.cnt % 50 == 0:
            print(self.cnt, score)

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

        return score,


    def run(self, day):
        self.day = day
        # gen_length = len(self.job_list)
        self.job_length = len(self.job_list)
        self.preheat_length = 0
        self.tempering_length = 0
        self.preheat_job_list = []
        self.tempering_job_list = []
        for job in self.job_list:
            if job['properties']['treatment']['preheat']:
                self.preheat_length += 1
                self.preheat_job_list.append(job)
            if len(job['properties']['treatment']['instruction']) >= 2 and job['properties']['treatment']['instruction'][1] == "T":
                self.tempering_length += 1
                self.tempering_job_list.append(job)
        # print('job length :', self.job_length)
        # print('preheating length :', self.preheat_length)
        # print('tempering length :', self.tempering_length)
        self.job_list.extend(self.preheat_job_list)
        self.job_list.extend(self.tempering_job_list)
        # print('job length :', len(self.job_list))


        gen_length = self.job_length + self.preheat_length + self.tempering_length
        print('gen length :', gen_length)

        print('--------------------------------')

        self.cnt = 0
        if gen_length == 0:
            mutation_indpb = 0
        else:
            mutation_indpb = float(1/gen_length)
        creator.create("FitnessMax", base.Fitness, weights=(-1.0,))
        creator.create("Individual", array.array, typecode='i', fitness=creator.FitnessMax)

        toolbox = base.Toolbox()

        # Attribute generator
        toolbox.register("furnaces", createIndividual, self.job_length, self.preheat_length, self.tempering_length)

        # Structure initializers
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.furnaces)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mate", multiCrossover, job_length=self.job_length, preheat_length=self.preheat_length,
                         tempering_length=self.tempering_length, indpb=0.2)
        toolbox.register("mutate", mutMultiFrom, job_length=self.job_length, preheat_length=self.preheat_length,
                         tempering_length=self.tempering_length, indpb=mutation_indpb) #0~6,7(미할당)까지 열처리로 있다는 뜻

        # :param tournsize: The number of individuals participating in each tournament.
        toolbox.register("select", tools.selTournament, tournsize=100)
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
        # print('population :', population)
        # exit(1)
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

        for g in range(0, self.ngen, 2):
            # Select the next generation individuals
            parents = toolbox.select(population, MAT_POOL_SIZE)

            # print('parents :', parents)

            # Clone the selected individuals
            offsprings = [toolbox.clone(ind) for ind in parents]
            # print('offspring :', offsprings)

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
                # print('eval. ind :', ind)
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
                    if pop.fitness.values[0] > best_so_far.fitness.values[0]:
                        best_so_far = pop
            self.best_list.append(best_so_far.fitness.values[0])
            #print('best so far', best_so_far.fitness.values[0], best_so_far)
        best = None
        for pop in population:
            if best is None:
                best = pop
            else:
                if pop.fitness.values[0] > best.fitness.values[0]:
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
    #
    # def score(self):
    #     E = self.simulator.total_results()
    #     T = self.simulator.total_time()
    #     T = (T - self.simulator.start_time).total_seconds()
    #     score = E * self.w1 + T * self.w2
    #     return score

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
