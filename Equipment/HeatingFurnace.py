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
        self.alloc.predictor.heating_time_prediction(self.name, self.current_job_list)
        if Debug_mode:
            print(self.name, ' :: calculate heating time')
        return random.randint(180, 300)

    def calc_holding_time(self, job):
        return random.randint(60, 180)

    def calc_door_time(self):
        return 10

    def calc_cooling_time(self):
        if Debug_mode:
            print(self.name, ' :: calculate cooling time')
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
                self.alloc.job_update(job, self.name, 'heating', self.name)
                if Debug_mode:
                    print(self.name, ' :: recharging ')
                    nPrint(job)

                reheating_time = self.alloc.predictor.reheating_time_prediction(self.name, self.current_job_list)
                for j in self.current_job_list:
                    j['properties']['last_process'] = 'holding'
                    j['properties']['last_process_end_time'] = self.env.now + reheating_time
                    j['properties']['last_heating_furnace'] = self.name


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

    def run(self):
        first_state = None
        last_log = None
        if len(self.log) != 0:
            i = 1
            last_log = self.log[len(self.log) - i]
            while last_log[1] not in ['idle', 'heating', 'keeping', 'cooling']:
                #print(self.log)
                #print(i)
                i += 1
                last_log = self.log[len(self.log) - i]
            #self.state = last_log[1]
            first_state = last_log[1]
            if last_log[3] != None and len(last_log[3]) != 0:
                current_job_id_list = last_log[3]
                for job_id in current_job_id_list:
                    for j in self.alloc.job:
                        if j['id'] == job_id:
                            self.current_job_list.append(j)
                            break

        if self.start_time != None:
            yield self.env.timeout(self.start_time)

        while True:
            # 작업 할당 받기
            if first_state == 'idle' or first_state == None:
                self.state = 'idle'
                if first_state != 'idle':
                    self.write_log('idle')
                new_job = self.alloc.heating_allocate(self.name, self.num, self.capacity)
                while new_job == None:
                    if self.num != 0:
                        if Debug_mode:
                            print(self.env.now, self.name, ' :: job list empty')
                        self.write_log('off')
                        self.env.exit()
                    yield self.env.timeout(10)
                    new_job = self.alloc.heating_allocate(self.name, self.num, self.capacity)
                if Debug_mode:
                    print(self.env.now, self.name, ' :: insertion')
                self.current_job_list.extend(new_job)
                current_job_id_list = []
                for j in self.current_job_list:
                    current_job_id_list.append(j['id'])
                self.write_log('insertion', current_job_id_list, current_job_id_list)
                if Debug_mode:
                    nPrint(self.current_job_list)
                    print(self.env.now, self.name, ' :: insertion complete')
                if first_state == 'idle':
                    first_state = 'heating'

            # 가열 시작
            if first_state == 'heating' or first_state == None:
                if first_state == 'heating' and last_log != None and last_log[1] == 'heating': # 원래 가열중이었다면
                    heating_end_time = last_log[2]
                    yield self.env.timeout(heating_end_time - self.env.now)
                else:
                    heating_time = self.calc_heating_time()
                    for j in self.current_job_list:
                        j['properties']['last_process'] = 'holding'
                        j['properties']['last_process_end_time'] = self.env.now + heating_time
                        j['properties']['last_heating_furnace'] = self.name
                    self.write_log('heating', self.env.now + heating_time, current_job_id_list)
                    if Debug_mode:
                        print(self.env.now, self.name, ' :: heating start')
                    self.state = 'heating'
                    yield self.env.timeout(heating_time)
                if Debug_mode:
                    print(self.env.now, self.name, ' :: heating complete')
                if first_state == 'heating':
                    first_state = 'keeping'

            # 키핑 시작
            if first_state == 'keeping' or first_state == None:
                self.write_log('keeping', None, current_job_id_list)
                if Debug_mode:
                    print(self.env.now, self.name, ' :: keeping')
                self.state = 'keeping'
                yield self.cycle_complete_wakeup.get()
                if Debug_mode:
                    print(self.env.now, self.name, ' :: cycle complete')
                first_state = 'cooling'

            # 냉각 시작
            if first_state == 'cooling' or first_state == None:
                if first_state == 'cooling' and last_log != None and last_log[1] == 'heating': # 원래 냉각중이었다면
                    cooling_end_time = last_log[2]
                    yield self.env.timeout(cooling_end_time - self.env.now)
                else:
                    cooling_time = self.calc_cooling_time()
                    self.write_log('cooling', self.env.now + cooling_time)
                    if Debug_mode:
                        print(self.env.now, self.name, ' :: cooling')
                    self.state = 'cooling'
                    yield self.env.timeout(cooling_time)
                if Debug_mode:
                    print(self.env.now, self.name, ' :: cooling complete')
                first_state = 'None'

            # 사이클 종료
            if len(self.current_job_list) != 0:
                print('cycle end. but job is exist!')
                print('name :', self.name)
                print('log :', self.log)
                exit(1)
            self.current_job_list = []