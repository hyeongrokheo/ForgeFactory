import random
from deap import creator
from deap import tools

def createIndividual(job_length, preheat_length, tempering_length):
    ind = []
    for i in range(job_length):
        ind.append(i)
    random.shuffle(ind)

    for i in range(preheat_length + tempering_length):
        ind.append(random.randrange(0,8))

    return ind

def multiCrossover(ind1, ind2, job_length, preheat_length, tempering_length, indpb):
    ind1_1 = ind1[0:job_length]
    ind1_2 = ind1[job_length : job_length + preheat_length + tempering_length]
    ind2_1 = ind2[0:job_length]
    ind2_2 = ind2[job_length : job_length + preheat_length + tempering_length]
    ind1_1, ind2_1 = tools.cxPartialyMatched(ind1_1, ind2_1)
    print('ind1 :', ind1_1, ind1_2)
    print('ind2 :', ind2_1, ind2_2)

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

# a,b = multiCrossover([1,5,3,2,4,0,6,6,4,1,2,3,5,7], [5,2,0,1,4,3,0,1,5,3,4,2,1,5], 6, 4, 4, 0.2)
# print('a :', a)
# print('b :', b)
# for i in range(10):
#     print(random.randrange(0, 7))