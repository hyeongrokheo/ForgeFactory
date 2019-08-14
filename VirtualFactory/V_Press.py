import random
from UtilFunction import *

class V_Press:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator
        self.num = num

        self.name = 'press_' + str(num + 1)

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

    def calc_press_time(self):
        press_time = self.alloc.predictor.forging_time_prediction(self.current_job)
        #print('press time :', press_time)
        return press_time

    def calc_press_energy(self, press_time):
        press_energy = self.alloc.predictor.forging_energy_prediction(press_time)
        return press_energy

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
            if first_state == 'press start':
                self.current_job = self.alloc.get_job(job_id)

        if self.start_time:
            yield self.env.timeout(self.start_time)

        while True:
            if Debug_mode2:
                print(3)
            if state == 'idle':
                first_state = None
                if len(self.todo) == 0:
                    self.write_log('off')
                    self.env.exit()
                target = self.todo[0]
                while target[1] != 'press start':
                    if Debug_mode2:
                        print(3)
                    self.todo.remove(target)
                    if len(self.todo) == 0:
                        self.write_log('off')
                        self.env.exit()
                    target = self.todo[0]
                self.current_job = self.alloc.get_next_press_job(self.name, target[2])
                # print('debug log :', self.env.now, self.current_job)
                if not self.current_job:
                    yield self.env.timeout(10)
                    continue
                self.todo.remove(target)
                if self.current_job == -1:
                    continue
                state = 'press start'

            if state == 'press start':
                if Debug_mode2:
                    print(3)
                if first_state:
                    first_state = None
                    press_time = self.calc_press_time()
                    press_energy = self.calc_press_energy(press_time)
                    press_end_time = last_log[0] + press_time
                    self.current_job['properties']['last_process_end_time'] = press_end_time
                    if press_end_time > self.env.now:
                        yield self.env.timeout(press_end_time - self.env.now)
                else:
                    press_time = self.calc_press_time()
                    press_energy = self.calc_press_energy(press_time)
                    press_end_time = self.env.now + press_time
                    self.current_job['properties']['current_equip'] = self.name
                    self.current_job['properties']['last_process'] = 'press'
                    self.current_job['properties']['last_process_end_time'] = press_end_time
                    self.write_log('press start', self.current_job['id'])
                    yield self.env.timeout(press_time)
                self.total_energy_usage += press_energy
            if Debug_mode2:
                print(3)
            state = 'idle'
            self.write_log('idle')
            self.alloc.end_job(self.current_job)