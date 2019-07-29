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
                new_job = self.alloc.get_next_treatment_job(self.name, self.capacity)
                if new_job == None:
                    yield self.env.timeout(30)
                    continue
                if new_job == []:
                    print('Error : treatment job 목록 비었음')
                    exit(1)
                self.current_job_list.extend(new_job)
                if first_state != None:
                    first_state = 'treatment start'

            current_job_id_list = []
            for j in self.current_job_list:
                current_job_id_list.append(j['id'])

            if first_state == 'treatment start' or first_state == None:
                if first_state == 'treatment start' and last_log != None and last_log[1] == 'treatment start':
                    treatment_time = self.calc_treatment_time()
                    if last_log[0] + treatment_time <= self.env.now:
                        self.write_info(0)
                    else:
                        self.write_info(last_log[0] + treatment_time - self.env.now)
                        yield self.env.timeout(last_log[0] + treatment_time - self.env.now)
                else:
                    self.write_log('treatment start', current_job_id_list)
                    treatment_time = self.calc_treatment_time()
                    treatment_energy = self.calc_treatment_energy(treatment_time)
                    self.total_energy_usage += treatment_energy
                    self.write_info(treatment_time)
                    yield self.env.timeout(treatment_time)

                self.write_log('treatment end')


            if Debug_mode:
                print(self.env.now, self.name, ':: treatment end')
                nPrint(self.current_job_list)
            first_state = None
            for j in self.current_job_list:
                self.alloc.end_job(j)

            self.current_job_list = []