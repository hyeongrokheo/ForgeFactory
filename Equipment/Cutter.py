import random
from copy import deepcopy
from UtilFunction import *

class Cutter:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator

        self.name = 'cutter_' + str(num + 1)

        self.current_job = None
        if Debug_mode:
            print(self.name + ' :: created')

        self.log = []

        self.start_time = None
        self.total_energy_usage = 0

    def set_env(self, start_time, log):
        self.start_time = start_time
        self.log = log

    def write_log(self, process, target=None):
        self.log.append([self.env.now, process, target])

    def calc_cut_time(self):
        cut_time = int(self.alloc.predictor.cutting_time_prediction(self.current_job) / 60)
        return cut_time

    def calc_cut_energy(self, cut_time):
        cut_energy = self.alloc.predictor.cutting_energy_prediction(cut_time)
        return cut_energy

    def run(self):
        state = 'idle'
        first_state = None
        self.current_job = None

        last_log = None
        if len(self.log) != 0:
            i = 1
            last_log = self.log[len(self.log) - i]
            state = last_log[1]
            first_state = last_log[1]
            job_id = last_log[2]
            if job_id:
                for j in self.alloc.job:
                    if j['id'] == job_id:
                        self.current_job = j
                        break

        if self.start_time:
            yield self.env.timeout(self.start_time)

        while True:
            if state == 'idle':
                first_state = None
                new_job = self.alloc.get_next_cut_job(self.name)
                while new_job == None:
                    yield self.env.timeout(10)
                    new_job = self.alloc.get_next_cut_job(self.name)

                self.current_job = new_job
                state = 'cutting start'

            if state == 'cutting start':
                if first_state:
                    first_state = None
                    cut_time = self.calc_cut_time()
                    cut_energy = self.calc_cut_energy(cut_time)
                    cut_end_time = last_log[0] + cut_time
                    self.current_job['properties']['last_process_end_time'] = cut_end_time
                    if cut_end_time > self.env.now:
                        yield self.env.timeout(cut_end_time - self.env.now)
                else:
                    cut_time = self.calc_cut_time()
                    cut_energy = self.calc_cut_energy(cut_time)
                    cut_end_time = self.env.now + cut_time
                    self.current_job['properties']['current_equip'] = self.name
                    self.current_job['properties']['last_process'] = 'cutting'
                    self.current_job['properties']['last_process_end_time'] = cut_end_time
                    self.write_log('cutting start', self.current_job['id'])
                    yield self.env.timeout(cut_time)
                self.total_energy_usage += cut_energy
                #self.write_log('cutting end', None)

            state = 'idle'
            self.write_log('idle')

            product_num = len(self.current_job['properties']['product_id_list'])
            if product_num == 1:
                self.alloc.end_job(self.current_job)
            else:
                for i in range(product_num):
                    job = deepcopy(self.current_job)
                    job['id'] += ('_' + str(i+1))
                    job['properties']['ingot']['current_weight'] /= product_num
                    self.alloc.job.append(job)
                    self.alloc.end_job(job)