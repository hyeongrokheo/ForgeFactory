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

    def calc_press_time(self):
        press_time = self.alloc.predictor.forging_time_prediction(self.current_job)
        if Debug_mode:
            print('press time :', press_time)
        return press_time

    def run(self):
        while True:
            self.current_job = self.alloc.get_next_press_job()
            if self.current_job == None:
                yield self.env.timeout(10)
                continue
            if Debug_mode:
                print(self.env.now, self.name, ':: press start')

            press_time = self.calc_press_time()
            #yield self.env.timeout(1)
            self.current_job['properties']['current_equip'] = self.name
            self.current_job['properties']['last_process'] = 'press'
            self.current_job['properties']['last_process_end_time'] = self.env.now + press_time
            # self.current_job['properties']['next_instruction'] += 1
            #if len(self.current_job['properties']['instruction_list'][0]) == self.current_job['properties']['next_instruction']:
            #    self.current_job['properties']['state'] = 'done'
            if Debug_mode:
                nPrint(self.current_job, ['last_process_end_time'])
            yield self.env.timeout(press_time)
            if Debug_mode:
                print(self.env.now, self.name, ':: press end')
                nPrint(self.current_job)

            #self.current_job['properties']['instruction_log'].append(self.name)
            self.alloc.end_job(self.current_job)
            #self.current_job = None
            #이거 해도 되나?? current job 저장된 본체가 사라지나..? 추후에 테스트 (굳이 안바꿔줘도 상관없긴 함)