import random
from UtilFunction import *

class V_Press:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator
        self.num = num

        self.name = 'press_' + str(num + 1)

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

    def calc_press_time(self):
        if Debug_mode:
            print(self.name, ' :: calculate press time')

        press_time = self.alloc.predictor.forging_time_prediction(self.current_job)
        return press_time

    def run(self):
        #print('press run', self.name)
        first_state = None
        last_log = None
        if len(self.log) != 0:
            i = 1
            last_log = self.log[len(self.log) - i]
            first_state = last_log[1]
            if first_state == 'press start':
                self.current_job = self.alloc.get_job(last_log[2])

        if self.start_time != None:
            yield self.env.timeout(self.start_time)

        while True:
            # idle
            #if self.num == 0:
                #print('log :', last_log, first_state, self.current_job)
            if first_state == 'idle' or first_state == None:
                target = self.todo[0]
                while target[1] != 'press start':
                    self.todo.remove(target)
                    if len(self.todo) == 0:
                        self.write_log('off')
                        self.env.exit()
                    target = self.todo[0]
                #if self.num == 0:
                    #print('t :', target)
                self.current_job = self.alloc.get_next_press_job(self.name, target[2])
                if self.current_job == None:
                    yield self.env.timeout(10)
                    continue
                if Debug_mode:
                    print(self.env.now, self.name, ':: press start')
                if first_state != None:
                    first_state = 'press start'
                self.todo.remove(target)

            if self.current_job == -1:
                first_state = None
                continue

            # press
            if first_state == 'press start' or first_state == None:
                if first_state == 'press start' and last_log != None and last_log[1] == 'press start':
                    job_id = last_log[2]
                    for j in self.alloc.job:
                        if j['id'] == job_id:
                            self.current_job = j
                            break
                    press_time = self.calc_press_time()
                    if last_log[0] + press_time <= self.env.now: # 예상완료시간이 현재 이전이라면 현재 시점으로
                        self.current_job['properties']['last_process_end_time'] = self.env.now
                    else:
                        self.current_job['properties']['last_process_end_time'] = last_log[0] + press_time
                        yield self.env.timeout(last_log[0] + press_time - self.env.now)
                else:
                    self.write_log('press start', self.current_job['id'])
                    press_time = self.calc_press_time()
                    self.current_job['properties']['current_equip'] = self.name
                    self.current_job['properties']['last_process'] = 'press'
                    self.current_job['properties']['last_process_end_time'] = self.env.now + press_time
                    if Debug_mode:
                        nPrint(self.current_job, ['last_process_end_time'])
                    yield self.env.timeout(press_time)

            # end
            self.write_log('press end', None)
            self.write_log('idle')
            self.alloc.end_job(self.current_job)
            first_state = None