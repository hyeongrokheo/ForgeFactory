import simpy
import random
from UtilFunction import *

class HeatingFurnace:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator
        self.num = num
        self.name = 'heating_furnace_' + str(num + 1).zfill(2)
        self.capacity = 200

        #self.recharging_wakeup = simpy.Store(self.env)
        self.cycle_complete_wakeup = simpy.Store(self.env)

        self.current_job_list = []
        self.state = None
        self.heating_end_time = None
        self.log = []

        self.start_time = None

        self.total_energy_usage = 0
        self.total_heating_weight = 0

        if Debug_mode:
            print(self.name + ' :: created')

    def set_env(self, start_time, log):
        #print(self.name, log)
        self.start_time = start_time
        self.log = log

    def get_data(self):
        return []

    def write_log(self, process, target=None, state=None):
        self.log.append([self.env.now, process, target, state])

    def calc_heating_time(self):
        heating_time = self.alloc.predictor.heating_time_prediction(self.name, self.current_job_list)
        return heating_time

    def calc_heating_energy(self, heating_time):
        heating_energy = self.alloc.predictor.heating_energy_prediction(self.name, self.current_job_list, heating_time)

        return heating_energy

    def calc_holding_time(self, job):
        return random.randint(60, 180)

    def calc_door_time(self):
        return 10

    def calc_cooling_time(self):
        return random.randint(60, 120)

    def recharging(self):
        while True:
            job = yield self.alloc.recharging_wakeup[self.num].get()
            if self.state == 'keeping':
                self.current_job_list.append(job)
                self.alloc.recharging_queue.remove(job)

                current_job_id_list = []
                for j in self.current_job_list:
                    current_job_id_list.append(j['id'])

                self.write_log('recharging', job['id'], current_job_id_list)
                self.alloc.job_update(job, self.name, 'holding', self.name)
                if Debug_mode:
                    print(self.name, ' :: recharging ')
                    nPrint(job)

                reheating_time = self.alloc.predictor.reheating_time_prediction(self.name, self.current_job_list)
                reheating_energy = self.alloc.predictor.reheating_energy_prediction(self.current_job_list, reheating_time)
                self.total_energy_usage += reheating_energy
                self.total_heating_weight += job['properties']['ingot']['current_weight']

                # job['properties']['last_process'] = 'holding'
                # job['properties']['last_heating_furncae'] = self.name
                # job['properties']['current_equip'] = self.name
                # job['properties']['next_instruction'] += 1
                for j in self.current_job_list:
                    #j['properties']['last_process'] = 'holding'
                    j['properties']['last_process_end_time'] = self.env.now + reheating_time
                    #j['properties']['last_heating_furnace'] = self.name


            #else:
                #job['properties']['last_heating_furnace'] = None
    def discharging(self):
        while True:
            # name, job = yield self.discharging_wakeup.get()
            discharging = yield self.alloc.discharging_wakeup[self.num].get()

            # print('discharging :', discharging)
            # print('name :', self.name)
            # print('press target job :', discharging[1])
            name = discharging[0]
            job = discharging[1]
            #print('discharging', self.name, name)
            # print('debug : name : ', name)
            yield self.env.timeout(0.1)
            if self.name == name:
                # print('debug : cj : ', self.current_job_list)
                # print('debug : tj : ', job)
                try:
                    self.current_job_list.remove(job)

                    current_job_id_list = []
                    for j in self.current_job_list:
                        current_job_id_list.append(j['id'])
                    self.write_log('discharging', job['id'], current_job_id_list)
                except:
                    #print('Error : discharging. but isnt exist')
                    None
                if Debug_mode:
                    print(self.name, ':: discharging ')
                    nPrint(job)
                if len(self.current_job_list) == 0:
                    count = 0
                    #for j in self.alloc.job:
                    #    if j['properties']['last_heating_furnace'] == self.name:
                    #        count += 1
                    #if count == 0:
                    self.cycle_complete_wakeup.put(True)

    def get_id_list(self, list):
        id_list = []
        for j in list:
            id_list.append(j['id'])
        return id_list

    def run(self):
        state = 'idle'
        first_state = None

        last_log = None
        if len(self.log) != 0:
            i = 1
            last_log = self.log[len(self.log) - i]
            while last_log[1] not in ['idle', 'heating', 'keeping', 'cooling', 'off']:
                i += 1
                last_log = self.log[len(self.log) - i]
            state = last_log[1]
            first_state = last_log[1]
            if last_log[3] and len(last_log[3]) != 0:
                current_job_id_list = last_log[3]
                for job_id in current_job_id_list:
                    for j in self.alloc.job:
                        if j['id'] == job_id:
                            self.current_job_list.append(j)
                            break

        if self.start_time:
            yield self.env.timeout(self.start_time)

        while True:
            # 작업 할당 받기
            if state == 'idle':
                first_state = None
                new_job = self.alloc.heating_allocate(self.name, self.num, self.capacity)
                while not new_job:
                    if self.num != 0:
                        state = 'off'
                        self.write_log('off')
                        #print(self.env.now, self.num, 'is off')
                        self.env.exit()
                    yield self.env.timeout(10)
                    new_job = self.alloc.heating_allocate(self.name, self.num, self.capacity)
                self.current_job_list = new_job
                current_job_id_list = self.get_id_list(self.current_job_list)
                self.write_log('insertion', current_job_id_list, current_job_id_list)

                if state != 'off':
                    state = 'heating'

                #self.write_log('heating', self.env.now + heating_time, current_job_id_list)

            # 가열 시작
            if state == 'heating':
                if first_state:
                    first_state = None
                    heating_time = self.calc_heating_time()
                    heating_end_time = last_log[0] + heating_time
                    for j in self.current_job_list:
                        j['properties']['last_process_end_time'] = heating_end_time
                    if heating_end_time > self.env.now:
                        yield self.env.timeout(heating_end_time - self.env.now)
                else:
                    heating_time = self.calc_heating_time()
                    heating_end_time = self.env.now + heating_time
                    for j in self.current_job_list:
                        j['properties']['current_equip'] = self.name
                        j['properties']['last_process'] = 'holding'
                        j['properties']['last_process_end_time'] = heating_end_time
                        j['properties']['last_heating_furnace'] = self.name
                        self.total_heating_weight += j['properties']['ingot']['current_weight']
                    self.write_log('heating', heating_end_time, current_job_id_list)
                    yield self.env.timeout(heating_time)

                state = 'keeping'
                self.write_log('keeping', None, current_job_id_list)
                self.alloc.end_job(self.current_job_list)

            # 키핑 시작
            if state == 'keeping':
                first_state = None
                yield self.cycle_complete_wakeup.get()

                state = 'cooling'
                self.write_log('cooling', None, current_job_id_list)

            # 냉각 시작
            if state == 'cooling':
                if first_state:
                    first_state = None
                    cooling_time = self.calc_cooling_time()
                    cooling_end_time = last_log[0] + cooling_time
                    if cooling_end_time > self.env.now:
                        yield self.env.timeout(cooling_end_time - self.env.now)
                else:
                    cooling_time = self.calc_cooling_time()
                    #cooling_end_time = self.env.now + cooling_time
                    yield self.env.timeout(cooling_time)
                state = 'idle'
                self.write_log('idle')

            if state == 'off':
                if not first_state:
                    self.write_log('off')
                self.env.exit()

            # 사이클 종료
            if len(self.current_job_list) != 0:
                print('cycle end. but job is exist!')
                print('name :', self.name)
                print('log :', self.log)
                exit(1)

            self.current_job_list = []
