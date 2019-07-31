import random
from UtilFunction import *

class TreatmentFurnace:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator

        self.name = 'treatment_furnace_' + str(num + 1)
        self.capacity = 150

        self.current_job_list = []
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

    def calc_treatment_time(self):
        if Debug_mode:
            print(self.name, ' :: calculate treatment time')

        treatment_time = self.alloc.predictor.treatment_time_prediction(self.name, self.current_job_list)
        return treatment_time

    def calc_treatment_energy(self, treatment_time):
        treatment_energy = self.alloc.predictor.treatment_energy_prediction(self.name, self.current_job_list, treatment_time)
        return treatment_energy

    def write_info(self, treatment_time):
        for j in self.current_job_list:
            j['properties']['current_equip'] = self.name
            j['properties']['last_process'] = 'treatment'
            j['properties']['last_process_end_time'] = self.env.now + treatment_time

    def get_id_list(self, list):
        id_list = []
        for j in list:
            id_list.append(j['id'])
        return id_list

    def run(self):
        state = 'idle'
        first_state = None
        self.current_job_list = []

        last_log = None
        if len(self.log) != 0:
            i = 1
            last_log = self.log[len(self.log) - i]
            state = last_log[1]
            first_state = last_log[1]
            if last_log[2] and len(last_log[2]) != 0:
                current_job_id_list = last_log[3]
                for job_id in current_job_id_list:
                    for j in self.alloc.job:
                        if j['id'] == job_id:
                            self.current_job_list.append(j)
                            break

        if self.start_time:
            yield self.env.timeout(self.start_time)

        while True:
            if state == 'idle':
                first_state = None
                new_job = self.alloc.get_next_treatment_job(self.name, self.capacity)
                while not new_job:
                    yield self.env.timeout(30)
                    new_job = self.alloc.get_next_treatment_job(self.name, self.capacity)
                self.current_job_list = new_job
                current_job_id_list = self.get_id_list(self.current_job_list)

                state = 'treatment start'

            if state == 'treatment start':
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
