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
        if Debug_mode:
            print(self.name + ' :: created')

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
                #형록
                #시간 다시계산코드 추가해야됨
                self.alloc.recharging_queue.remove(job)
                if Debug_mode:
                    print(self.name, ' :: recharging ')
                    nPrint(job)
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
            if self.name == name:
                # print('debug : cj : ', self.current_job_list)
                # print('debug : tj : ', job)
                try:
                    self.current_job_list.remove(job)
                except:
                    None
                if Debug_mode:
                    print(self.name, ':: discharging ')
                    nPrint(job)
                if len(self.current_job_list) == 0:
                    self.cycle_complete_wakeup.put(True)

    def run(self):
        while True:
            # 작업 할당 받기
            self.state = 'idle'
            new_job = self.alloc.heating_allocate(self.name, self.capacity)
            while new_job == None:
                if self.num != 0:
                    print(self.env.now, self.name, ' :: job list empty')
                    self.env.exit()
                yield self.env.timeout(10)
                new_job = self.alloc.heating_allocate(self.name, self.capacity)
            if Debug_mode:
                print(self.env.now, self.name, ' :: insertion')
            # print('debug : alloc : ', all)
            self.current_job_list.extend(new_job)
            # if len(self.current_job_list) == 0:
            #print('job list :', self.current_job_list)
            if Debug_mode:
                nPrint(self.current_job_list)
                print(self.env.now, self.name, ' :: insertion complete')

            # 가열 시작
            heating_time = self.calc_heating_time()
            for j in self.current_job_list:
                #j['properties']['current_equip'] = self.name
                #j['properties']['last_process'] = 'heating'
                j['properties']['last_process_end_time'] = self.env.now + heating_time
                # j['properties']['instruction_log'].append(self.name)
                j['properties']['last_heating_furnace'] = self.name
                # j['properties']['next_instruction'] += 1
            if Debug_mode:
                print(self.env.now, self.name, ' :: heating start')
            self.state = 'heating'
            yield self.env.timeout(heating_time)
            if Debug_mode:
                print(self.env.now, self.name, ' :: heating complete')

            """
            job별로 holding time 예측해서 완료시각 기록
            """
            for j in self.current_job_list:
                # print(j['properties'])
                j['properties']['last_process'] = 'holding'
                j['properties']['last_process_end_time'] = self.env.now + self.calc_holding_time(j)
                # j['properties']['next_instruction'] += 1

            # 키핑 시작
            if Debug_mode:
                print(self.env.now, self.name, ' :: keeping')
            self.state = 'keeping'
            # for j in self.current_job_list:
            # if len(self.current_job['properties']['instruction_list'][0]) == self.current_job['properties']['next_instruction']:
            # self.current_job['properties']['state'] = 'done'
            yield self.cycle_complete_wakeup.get()
            if Debug_mode:
                print(self.env.now, self.name, ' :: cycle complete')

            # 냉각 시작
            cooling_time = self.calc_cooling_time()
            if Debug_mode:
                print(self.env.now, self.name, ' :: cooling')
            self.state = 'cooling'
            yield self.env.timeout(cooling_time)
            if Debug_mode:
                print(self.env.now, self.name, ' :: cooling complete')

            if len(self.current_job_list) != 0:
                print('cycle end. but job is exist!')
                exit(1)
            self.current_job_list = []

    """def __init__(self, env, allocator, num):
        self.env = env
        self.name = 'heating_furnace_' + str(num + 1)
        self.state = 'idle'
        self.allocator = allocator
        self.capacity = simpy.Store(env, 120) # container

        self.current_job_list = []
        #self.success_job_list = [['job1', ~~, ~~], []]
        #self
        #self.current_capacity = 100
        print(self.name + ' :: created')

    def clear(self):
        self.current_job_list = []
        self.success_job_list = []

    def heating(self):
        print('HeatingFurnace :: heating')
        self.state = 'heating'
        yield self.env.timeout(60)
        print('HeatingFurnace :: heating complete')
        self.state = 'idle'

    '''def request(self):
        #while True:
        yield self.env.timeout(555)
        print('HeatingFurnace :: request')
        yield self.allocator.request.succeed()
        print('HeatingFurnace :: allocated')'''

    def run(self):
        None
        #while True:
            #print('run' + self.name)
            #self.clear()
            #self.env.run(self.env.process(self.insertion()))
            #self.calc_heating_time()
            #print(self.env.run(self.env.process(self.calc_heating_time())))
            #self.env.run(self.env.process(self.heating()))
            #time.sleep(3)"""