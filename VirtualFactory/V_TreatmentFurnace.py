import random
from UtilFunction import *

class V_TreatmentFurnace:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator

        self.name = 'treatment_furnace_' + str(num + 1)
        self.capacity = 150

        self.current_job_list = []
        if Debug_mode:
            print(self.name + ' :: created')

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

    def calc_treatment_time(self):
        if Debug_mode:
            print(self.name, ' :: calculate treatment time')

        treat_time = self.alloc.predictor.treatment_time_prediction(self.name, self.current_job_list)
        return treat_time

    def calc_treatment_energy(self, treatment_time):
        treatment_energy = self.alloc.predictor.treatment_energy_prediction(self.name, self.current_job_list, treatment_time)
        return treatment_energy

    def write_info(self, treatment_time):
        for j in self.current_job_list:
            j['properties']['current_equip'] = self.name
            j['properties']['last_process'] = 'treatment'
            j['properties']['last_process_end_time'] = self.env.now + treatment_time

    def get_id_list(self, list):
        if list == None:
            return None
        id_list = []
        for j in list:
            id_list.append(j['id'])
        return id_list

    def run(self):
        state = 'idle'
        last_log = None
        self.current_job_list = []
        if len(self.log) != 0:
            i = 1
            last_log = self.log[len(self.log) - i]
            state = last_log[1]
            first_state = last_log[1]

            if last_log[2] and len(last_log[2]) != 0:
                current_job_id_list = last_log[2]
                for job_id in current_job_id_list:
                    for j in self.alloc.job:
                        if j['id'] == job_id:
                            self.current_job_list.append(j)
                            break

        if self.start_time:
            yield self.env.timeout(self.start_time)

        # print(self.env.now, self.name, state, self.get_id_list(self.current_job_list), self.todo)

        while True:
            if Debug_mode2:
                print(1)
            if state == 'idle':
                first_state = None
                if len(self.todo) == 0:
                    self.write_log('off')
                    self.env.exit()
                target = self.todo[0]
                while target[1] != 'treatment start':
                    if Debug_mode2:
                        print(1)
                    self.todo.remove(target)
                    if len(self.todo) == 0:
                        self.write_log('off')
                        self.env.exit()
                    target = self.todo[0]
                self.todo.remove(target)

                target_id_list = target[2]
                self.current_job_list = None
                while not self.current_job_list:
                    if Debug_mode2:
                        print(1)
                    self.current_job_list = self.alloc.get_next_treatment_job(self.name, target_id_list)
                    # print('try get :', target_id_list, self.get_id_list(self.current_job_list))
                    if not self.current_job_list:
                        yield self.env.timeout(30)
                if self.current_job_list == -1:
                    first_state = None
                    continue

                current_job_id_list = self.get_id_list(self.current_job_list)
                state = 'treatment start'

            if state == 'treatment start':
                # print(self.env.now, self.name, 'treatment start', current_job_id_list)
                if first_state:
                    first_state = None
                    treatment_time = self.calc_treatment_time()
                    treatment_energy = self.calc_treatment_energy(treatment_time)
                    treatment_end_time = last_log[0] + treatment_time
                    for j in self.current_job_list:
                        j['properties']['last_process_end_time'] = treatment_end_time
                    if treatment_end_time > self.env.now:
                        yield self.env.timeout(treatment_end_time - self.env.now)
                else:
                    treatment_time = self.calc_treatment_time()
                    treatment_energy = self.calc_treatment_energy(treatment_time)
                    treatment_end_time = self.env.now + treatment_time
                    for j in self.current_job_list:
                        j['properties']['current_equip'] = self.name
                        j['properties']['last_process'] = 'treatment'
                        j['properties']['last_process_end_time'] = treatment_end_time
                    self.write_log('treatment start', current_job_id_list)
                    yield self.env.timeout(treatment_time)

                for j in self.current_job_list:
                    self.alloc.end_job(j)
                state = 'idle'
                self.write_log('idle')
                self.total_energy_usage += treatment_energy

            self.current_job_list = []