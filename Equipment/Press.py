import random
from UtilFunction import *

class Press:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator

        self.name = 'press_' + str(num + 1)

        self.current_job = None
        if Debug_mode:
            print(self.name + ' :: created')

        self.log = []

        self.start_time = None

    def set_env(self, start_time, log):
        self.start_time = start_time
        self.log = log

    def write_log(self, process, target=None):
        self.log.append([self.env.now, process, target])

    def calc_press_time(self):
        if Debug_mode:
            print(self.name, ' :: calculate press time')

        press_time = self.alloc.predictor.forging_time_prediction(self.current_job)
        return press_time

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
                self.current_job = self.alloc.get_next_press_job(self.name)
                if self.current_job == None:
                    yield self.env.timeout(10)
                    continue
                if Debug_mode:
                    print(self.env.now, self.name, ':: press start')
                if first_state != None:
                    first_state = 'press start'

            if first_state == 'press start' or first_state == None:
                if first_state == 'press start' and last_log != None and last_log[1] == 'press start':
                    press_time = self.calc_press_time()
                    if last_log[0] + press_time <= self.env.now: # 예상완료시간이 현재 이전이라면 현재 시점으로
                        self.current_job['properties']['last_process_end_time'] = self.env.now
                    else:
                        self.current_job['properties']['last_process_end_time'] = last_log[0] + press_time
                        yield self.env.timeout(self.current_job['properties']['last_process_end_time'] - self.env.now)
                else:
                    self.write_log('press start', self.current_job['id'])
                    press_time = self.calc_press_time()
                    self.current_job['properties']['current_equip'] = self.name
                    self.current_job['properties']['last_process'] = 'press'
                    self.current_job['properties']['last_process_end_time'] = self.env.now + press_time
                    if Debug_mode:
                        nPrint(self.current_job, ['last_process_end_time'])
                    yield self.env.timeout(press_time)

            self.write_log('press end', None)
            if Debug_mode:
                print(self.env.now, self.name, ':: press end')
                nPrint(self.current_job)

            self.alloc.end_job(self.current_job)
            first_state = None