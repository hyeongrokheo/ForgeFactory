import simpy
import random
from UtilFunction import *

class V_HeatingFurnace:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator
        self.num = num
        self.name = 'heating_furnace_' + str(num + 1).zfill(2)
        self.capacity = 200

        #self.recharging_wakeup = simpy.Store(self.env)
        self.cycle_complete_wakeup = simpy.Store(self.env)

        self.current_job_list = []
        self.heating_end_time = None
        self.log = []

        self.start_time = None
        self.todo = None

        self.total_heating_weight = 0
        self.total_energy_usage = 0

        if Debug_mode:
            print(self.name + ' :: created')

    def set_env(self, start_time, log):
        #print(self.name, log)
        self.start_time = start_time
        self.log = log

    def set_todo(self, log):
        self.todo = log
        self.recharging_todo = []
        for l in self.todo:
            if l[1] == 'recharging':
                self.recharging_todo.append(l)

    # def get_data(self):
    #     return []

    def write_log(self, process, target=None, state=None):
        self.log.append([self.env.now, process, target, state])

    def calc_heating_time(self):
        heating_time = self.alloc.predictor.heating_time_prediction(self.name, self.current_job_list)
        # print('calc heating time :', heating_time)
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
            if self.state == 'keeping':
                if len(self.recharging_todo) == 0:
                    self.write_log('off')
                    self.env.exit()
                target = self.recharging_todo[0]
                target_id = target[2]
                #print('in HF, target id :', target_id)
                job = self.alloc.recharging(target_id)
                if job != None:
                    self.current_job_list.append(job)
                    job['properties']['next_instruction'] += 1
                    self.recharging_todo.remove(target)
                    current_job_id_list = []
                    for j in self.current_job_list:
                        current_job_id_list.append(j['id'])
                    self.write_log('recharging', job['id'], current_job_id_list)
                    reheating_time = self.alloc.predictor.reheating_time_prediction(self.name, self.current_job_list)
                    reheating_energy = self.alloc.predictor.reheating_time_prediction(self.current_job_list, reheating_time)
                    self.total_energy_usage += reheating_energy
                    self.total_heating_weight += job['properties']['ingot']['current_weight']
                    for j in self.current_job_list:
                        j['properties']['last_process'] = 'holding'
                        j['properties']['last_process_end_time'] = self.env.now + reheating_time
                        j['properties']['last_heating_furnace'] = self.name
                else:
                    yield self.env.timeout(10)
            else:
                yield self.env.timeout(10)

    def discharging(self):
        # if self.start_time:
        #     yield self.env.timeout(self.start_time)

        while True:
            discharging = yield self.alloc.discharging_wakeup[self.num].get()

            name = discharging[0]
            job = discharging[1]
            yield self.env.timeout(0.1)
            if self.name == name:
                #print('discharging', self.env.now, self.name, job['id'])
                #print('job list :', self.get_id_list(self.current_job_list))
                try:
                    self.current_job_list.remove(job)
                    current_job_id_list = []
                    for j in self.current_job_list:
                        current_job_id_list.append(j['id'])
                    self.write_log('discharging', job['id'], current_job_id_list)
                except:
                    # print('Error : discharging. but isnt exist')
                    None
                if len(self.current_job_list) == 0:
                    self.cycle_complete_wakeup.put(True)

    def get_id_list(self, list):
        id_list = []
        for j in list:
            id_list.append(j['id'])
        return id_list

    def run(self):
        # print(self.name, 'run')
        self.state = 'idle'
        first_state = None
        current_job_id_list = None
        last_log = None
        if len(self.log) != 0:
            i = 1
            last_log = self.log[len(self.log) - i]
            while last_log[1] not in ['idle', 'heating', 'keeping', 'cooling']:
                i += 1
                last_log = self.log[len(self.log) - i]
            self.state = last_log[1]
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

        # print(self.env.now, self.name, self.state, self.current_job_list)
        # print('debug state :', self.state)
        while True:
            #print(self.env.now, self.name, 'state :', self.state)
            #print(self.env.now, self.name, 'current job list :', self.current_job_list)
            # 작업 할당 받기
            # print(self.env.now, self.name, self.state, 'idle start', self.current_job_list)
            if self.state == 'idle':
                first_state = None

                self.current_job_list = []
                while (not self.current_job_list) or len(self.current_job_list) == 0:
                    if len(self.todo) == 0:
                        print('no todo')
                    target = self.todo[0]
                    self.todo.remove(target)
                    while target[1] != 'insertion':
                        if len(self.todo) == 0:
                            print('no todo')
                        target = self.todo[0]
                        self.todo.remove(target)

                    target_id_list = target[2]

                    self.current_job_list = self.alloc.heating_allocate(self.name, target_id_list)

                    while self.current_job_list == None or self.current_job_list == -1:
                        # print(self.env.now, self.current_job_list)
                        #여기서 무한루프
                        if self.current_job_list == None:
                            self.current_job_list = []
                            yield self.env.timeout(10)
                            self.current_job_list = self.alloc.heating_allocate(self.name, target_id_list)
                        elif self.current_job_list == -1:
                            self.current_job_list = []
                            self.state = 'idle'
                    #
                    # if self.current_job_list:
                    #     if self.current_job_list == -1:
                    #         self.current_job_list = None
                    #         continue
                    #     else:
                    #         self.state = 'heating'
                    #         current_job_id_list = self.get_id_list(self.current_job_list)
                    #         self.write_log('insertion', current_job_id_list, current_job_id_list)
                    # else:
                    #     yield self.env.timeout(10)
            if self.state == 'idle':
                continue
            # 가열 시작
            # print(self.env.now, self.name, self.state, 'heating start', self.current_job_list)
            if self.state == 'heating':
                if first_state:
                    first_state = None
                    heating_time = self.calc_heating_time()
                    heating_energy = self.calc_heating_energy(heating_time)
                    heating_end_time = last_log[0] + heating_time
                    for j in self.current_job_list:
                        j['properties']['last_process_end_time'] = heating_end_time
                    if heating_end_time > self.env.now:
                        yield self.env.timeout(heating_end_time - self.env.now)
                else:
                    heating_time = self.calc_heating_time()
                    heating_energy = self.calc_heating_energy(heating_time)
                    heating_end_time = self.env.now + heating_time
                    for j in self.current_job_list:
                        j['properties']['current_equip'] = self.name
                        j['properties']['last_process'] = 'holding'
                        # j['properties']['next_instruction'] += 1
                        j['properties']['last_process_end_time'] = heating_end_time
                        j['properties']['last_heating_furnace'] = self.name
                        self.total_heating_weight += j['properties']['ingot']['current_weight']
                    self.write_log('heating', heating_end_time, current_job_id_list)
                    yield self.env.timeout(heating_time)

                self.total_energy_usage += heating_energy
                self.state = 'keeping'
                self.write_log('keeping', None, current_job_id_list)
                self.alloc.end_job(self.current_job_list)

            # 키핑 시작
            if self.state == 'keeping':
                first_state = None
                yield self.cycle_complete_wakeup.get()

                self.state = 'cooling'
                self.write_log('cooling', None, current_job_id_list)
            # print(self.env.now, self.name, 'keeping end', self.current_job_list)
            # 냉각 시작
            if self.state == 'cooling':
                if first_state:
                    first_state = None
                    cooling_time = self.calc_cooling_time()
                    cooling_end_time = last_log[0] + cooling_time
                    if cooling_end_time > self.env.now:
                        yield self.env.timeout(cooling_end_time - self.env.now)
                else:
                    cooling_time = self.calc_cooling_time()
                    yield self.env.timeout(cooling_time)
                    self.state = 'idle'

            if self.state == 'off':
                if not first_state:
                    self.write_log('off')
                self.env.exit()

            # 사이클 종료
            # print(self.env.now, self.name, 'cycle end', self.current_job_list)
            if len(self.current_job_list) != 0:
                print(self.env.now, 'cycle end. but job is exist!')
                print('state :', self.state)
                print('name :', self.name)
                print('log :', self.log)
                exit(1)
            self.current_job_list = []