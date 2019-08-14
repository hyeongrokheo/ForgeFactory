import random
from copy import deepcopy
from UtilFunction import *

class V_Cutter:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator
        self.num = num

        self.name = 'cutter_' + str(num + 1)

        self.current_job = None

        self.log = []
        self.todo = None

        self.start_time = None
        self.total_energy_usage = 0

    def set_env(self, start_time, log):
        self.start_time = start_time
        self.log = log

    def set_todo(self, log):
        self.todo = log

    def write_log(self, process, target=None):
        self.log.append([self.env.now, process, target])

    def calc_cut_time(self):
        cut_time = self.alloc.predictor.cutting_time_prediction(self.current_job)
        return cut_time

    def calc_cut_energy(self, cut_time):
        cut_energy = self.alloc.predictor.cutting_energy_prediction(cut_time)
        return cut_energy

    def run(self):
        state = 'idle'
        first_state = None
        last_log = None

        if len(self.log) != 0:
            i = 1
            last_log = self.log[len(self.log) - i]
            state = last_log[1]
            first_state = last_log[1]
            job_id = last_log[2]
            if first_state == 'cutting start':
                self.current_job = self.alloc.get_job(job_id)

        if self.start_time:
            yield self.env.timeout(self.start_time)
        # print('v cutter log :', state, first_state, last_log)
        while True:
            if Debug_mode2:
                print(2)
            if state == 'idle':
                if Debug_mode2:
                    print(2)
                first_state = None
                if len(self.todo) == 0:
                    if Debug_mode2:
                        print(2)
                    yield self.env.timeout(self.start_time + 60 * 24 - self.env.now)
                    continue
                target = self.todo[0]
                while target[1] != 'cutting start':
                    if Debug_mode2:
                        print(2)
                    self.todo.remove(target)
                    if len(self.todo) == 0:
                        yield self.env.timeout(self.start_time + 60 * 24 - self.env.now)
                        continue
                    target = self.todo[0]
                self.current_job = self.alloc.get_next_cut_job(self.name, target[2])
                #print(self.env.now, target[2], self.current_job)
                if not self.current_job:
                    if Debug_mode2:
                        print(2)
                    yield self.env.timeout(10)
                    continue
                self.todo.remove(target)
                if self.current_job == -1:
                    continue
                state = 'cutting start'

            if state == 'cutting start':
                if Debug_mode2:
                    print(2)
                if first_state:
                    first_state = None
                    cut_time = self.calc_cut_time()
                    cut_energy = self.calc_cut_energy(cut_time)
                    cut_end_time = last_log[0] + cut_time
                    self.current_job['properties']['last_process_end_time'] = cut_end_time
                    if cut_end_time > self.env.now:
                        yield self.env.timeout(cut_end_time - self.env.now)
                else:
                    if Debug_mode2:
                        print(2)
                    cut_time = self.calc_cut_time()
                    cut_energy = self.calc_cut_energy(cut_time)
                    cut_end_time = self.env.now + cut_time
                    self.current_job['properties']['current_equip'] = self.name
                    self.current_job['properties']['last_process'] = 'cutting'
                    self.current_job['properties']['last_process_end_time'] = cut_end_time
                    self.write_log('cutting start', self.current_job['id'])
                    yield self.env.timeout(cut_time)
                self.total_energy_usage += cut_energy

            state = 'idle'
            self.write_log('idle')

            product_num = len(self.current_job['properties']['product_id_list'])
            if Debug_mode2:
                print(2)
            if product_num == 1:
                self.alloc.end_job(self.current_job)
            else:
                for i in range(product_num):
                    job = deepcopy(self.current_job)
                    job['id'] += ('_' + str(i+1))
                    job['properties']['ingot']['current_weight'] /= product_num
                    self.alloc.job.append(job)
                    self.alloc.end_job(job)