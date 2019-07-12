import random
from UtilFunction import *

class TreatmentFurnace:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator

        self.name = 'treatment_furnace_' + str(num + 1)
        self.capacity = 150

        self.current_job_list = []
        if Debug_mode:
            print(self.name + ' :: created')

        self.log = []

    def write_log(self, process, target=None):
        self.log.append([self.env.now, process, target])

    def calc_treatment_time(self):
        if Debug_mode:
            print(self.name, ' :: calculate treatment time')

        treat_time = self.alloc.predictor.treatment_time_prediction(self.name, self.current_job_list)
        return treat_time

    def run(self):
        while True:
            new_job = self.alloc.get_next_treatment_job(self.name, self.capacity)
            if new_job == None:
                yield self.env.timeout(30)
                continue
            if new_job == []:
                print('Error : treatment job 목록 비었음')
                exit(1)
            self.current_job_list.extend(new_job)

            if Debug_mode:
                print(self.env.now, self.name, ':: treatment start')
                nPrint(self.current_job_list)

            self.write_log('treatment start', self.current_job_list)
            treatment_time = self.calc_treatment_time()
            for j in self.current_job_list:
                j['properties']['current_equip'] = self.name
                j['properties']['last_process'] = 'treatment'
                j['properties']['last_process_end_time'] = self.env.now + treatment_time

            yield self.env.timeout(treatment_time)

            self.write_log('treatment end')
            if Debug_mode:
                print(self.env.now, self.name, ':: treatment end')
                nPrint(self.current_job_list)

            for j in self.current_job_list:
                self.alloc.end_job(j)
            self.write_log('idle')
            self.current_job_list = []