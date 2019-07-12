import random
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

    def write_log(self, process, target=None):
        self.log.append([self.env.now, process, target])

    def calc_cut_time(self):
        if Debug_mode:
            print(self.name, ' :: calculate cut time')
        cut_time = int(self.alloc.predictor.cutting_time_prediction(self.current_job) / 60)
        return cut_time

    def run(self):
        while True:
            self.write_log('idle')
            self.current_job = self.alloc.get_next_cut_job(self.name)
            if self.current_job == None:
                yield self.env.timeout(10)
                continue
            if Debug_mode:
                print(self.env.now, self.name, ':: cut start')

            self.write_log('cutting start', self.current_job)
            cut_time = self.calc_cut_time()
            self.current_job['properties']['current_equip'] = self.name
            self.current_job['properties']['last_process'] = 'cut'
            self.current_job['properties']['last_process_end_time'] = self.env.now + cut_time
            if Debug_mode:
                nPrint(self.current_job, ['last_process_end_time'])

            yield self.env.timeout(cut_time)

            self.write_log('cut end', self.current_job)
            if Debug_mode:
                print(self.env.now, self.name, ':: cut end')
                nPrint(self.current_job)

            #self.current_job['properties']['instruction_log'].append(self.name)
            self.alloc.end_job(self.current_job)