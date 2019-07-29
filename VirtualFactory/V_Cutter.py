import random
from copy import deepcopy
from UtilFunction import *

class V_Cutter:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator

        self.name = 'cutter_' + str(num + 1)

        self.current_job = None
        if Debug_mode:
            print(self.name + ' :: created')

        self.log = []
        self.todo = None

        self.start_time = None

    def set_env(self, start_time, log):
        self.start_time = start_time
        self.log = log

    def set_todo(self, log):
        self.todo = log

    def write_log(self, process, target=None):
        self.log.append([self.env.now, process, target])

    def calc_cut_time(self):
        if Debug_mode:
            print(self.name, ' :: calculate cut time')

        cut_time = int(self.alloc.predictor.cutting_time_prediction(self.current_job) / 60)
        return cut_time

    def run(self):
        first_state = None
        last_log = None
        if len(self.log) != 0:
            i = 1
            last_log = self.log[len(self.log) - i]
            first_state = last_log[1]

        if self.start_time != None:
            yield self.env.timeout(self.start_time)

        while True:
            if first_state == 'idle' or first_state == None:
                if first_state == None:
                    self.write_log('idle')
                target = self.todo[0]
                while target[1] != 'cutting start':
                    self.todo.remove(target)
                    if len(self.todo) == 0:
                        self.write_log('off')
                        self.env.exit()
                    target = self.todo[0]

                self.current_job = self.alloc.get_next_cut_job(self.name, target[2])
                if self.current_job == None:
                    yield self.env.timeout(10)
                    continue
                if Debug_mode:
                    print(self.env.now, self.name, ':: cut start')
                if first_state != None:
                    first_state = 'cutting start'
                self.todo.remove(target)

            if self.current_job == -1:
                first_state = None
                continue

            if first_state == 'cutting start' or first_state == None:
                print('cut start', self.current_job['id'])
                if first_state ==  'cutting start' and last_log != None and last_log[1] == 'cutting start':
                    job_id = last_log[2]
                    for j in self.alloc.job:
                        if j['id'] == job_id:
                            self.current_job = j
                            break
                    cut_time = self.calc_cut_time()
                    if last_log[0] + cut_time <= self.env.now: # 예상완료시간이 현재 이전이라면 현재 시점으로
                        self.current_job['properties']['last_process_end_time'] = self.env.now
                    else:
                        self.current_job['properties']['last_process_end_time'] = last_log[0] + cut_time
                        yield self.env.timeout(self.current_job['properties']['last_process_end_time'] - self.env.now)
                else:
                    self.write_log('cutting start', self.current_job['id'])
                    cut_time = self.calc_cut_time()
                    self.current_job['properties']['current_equip'] = self.name
                    self.current_job['properties']['last_process'] = 'cut'
                    self.current_job['properties']['last_process_end_time'] = self.env.now + cut_time
                    if Debug_mode:
                        nPrint(self.current_job, ['last_process_end_time'])
                    yield self.env.timeout(cut_time)

            self.write_log('cut end', self.current_job['id'])
            if Debug_mode:
                print(self.env.now, self.name, ':: cut end')
                nPrint(self.current_job)

            product_num = len(self.current_job['properties']['product_id_list'])
            if product_num == 1:
                self.alloc.end_job(self.current_job)
            else:
                for i in range(product_num):
                    job = deepcopy(self.current_job)
                    job['id'] += ('_' + str(i))
                    self.alloc.end_job(job)

            first_state = None