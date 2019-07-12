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

    def write_log(self, process, target=None):
        self.log.append([self.env.now, process, target])

    def calc_press_time(self):
        if Debug_mode:
            print(self.name, ' :: calculate press time')

        press_time = self.alloc.predictor.forging_time_prediction(self.current_job)
        return press_time

    def run(self):
        while True:
            self.current_job = self.alloc.get_next_press_job(self.name)
            if self.current_job == None:
                yield self.env.timeout(10)
                continue
            if Debug_mode:
                print(self.env.now, self.name, ':: press start')

            self.write_log('press start', self.current_job)
            press_time = self.calc_press_time()
            self.current_job['properties']['current_equip'] = self.name
            self.current_job['properties']['last_process'] = 'press'
            self.current_job['properties']['last_process_end_time'] = self.env.now + press_time
            if Debug_mode:
                nPrint(self.current_job, ['last_process_end_time'])

            yield self.env.timeout(press_time)

            self.write_log('press end', self.current_job)
            if Debug_mode:
                print(self.env.now, self.name, ':: press end')
                nPrint(self.current_job)

            self.alloc.end_job(self.current_job)
            self.write_log('idle')