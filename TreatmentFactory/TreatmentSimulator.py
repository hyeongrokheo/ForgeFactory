from TreatmentFactory.TreatmentFurnace import *
from TreatmentFactory.TreatmentAllocator import *
from UtilFunction import *
import simpy

from copy import *

# 열처리로 스펙 : 중량, len1, len2 , len3
furnace_specification = [[120, 10700, 2000, 3490],
                         [150, 13450, 2000, 3490],
                         [200, 11500, 3000, 5200],
                         [200, 11500, 3000, 5600],
                         [200, 11500, 3000, 5600],
                         [120, 10700, 2000, 3490],
                         [150, 16400, 2000, 3490]]

# simpy에 대하여..
# 시간은 env 기준으로 흐름. env가 새롭게 정의되지 않는 한 계속 이어서 시뮬레이션 가능함

class TreatmentSimulator:
    def __init__(self, predictor, type, treatment_job_list=None):
        # parameter
            # predictor
            # type : 'GA', 'Heuristic'
            # treatment_job_list : 열처리 대상 작업 목록
        self.env = None
        self.type = type
        self.predictor = predictor
        self.alloc = None
        self.original_treatment_job_list = treatment_job_list
        self.treatment_job_list = None
        self.treatment_furnace_list = None
        self.job_length = None
        self.preheat_length = None
        self.tempering_length = None
        self.penalty_count = 0

    def init_job(self, job_list):
        self.original_treatment_job_list = job_list

    # env 생성
    # 공장 초기화 (열처리로 생성)
    def init_simulator(self):
        self.env = simpy.Environment()

        self.treatment_furnace_list = []
        for i in range(len(furnace_specification)):
            tf = TreatmentFurnace(self.env, None, furnace_specification[i], i)
            self.treatment_furnace_list.append(tf)

    # 작업 내용 갱신
    def re_init_simulator(self, treatment_job_list, individual, job_length, preheat_length, tempering_length, update=None, last_env=None, H_TF_Plan = None):
        # print('in re init simulator, now :', self.env.now)

        self.original_treatment_job_list = deepcopy(treatment_job_list)
        self.job_length = job_length
        self.preheat_length = preheat_length
        self.tempering_length = tempering_length
        self.treatment_job_list = deepcopy(self.original_treatment_job_list)

        # print('debug 2')
        if self.type == 'GA':
            # print('debug 5')
            self.alloc = TreatmentAllocator(self.env, self.type, self.predictor, self.treatment_job_list,
                                            deepcopy(individual), self.job_length, self.preheat_length, self.tempering_length, last_env)
            # print('debug 3')
        elif self.type == 'Heuristic':
            # print('debug 6')
            self.alloc = TreatmentAllocator(self.env, self.type, self.predictor, self.treatment_job_list,
                                            None, None, None, None, last_env)
            # print('debug 4')
        else:
            print('simulator type error :', self.type)
            exit(1)
        if H_TF_Plan:
            self.alloc.furnace_log = H_TF_Plan
        # print('debug 3')

        for tf in self.treatment_furnace_list:
            tf.set_alloc(self.alloc)
        # print('debug 1')


    # def set_job_queue(self, individual):
    #     self.alloc.set_job_queue(individual)

    # def set_envs(self, envs):
    #     #print('Log :', envs['heating_furnace'][0])
    #     self.start_time = envs['time']
    #     allocator_data = envs['allocator']
    #     self.alloc.set_env(self.start_time, allocator_data)
    #     heating_furnace_logs = envs['heating_furnace']
    #     for i in range(len(self.heating_furnace_list)):
    #         self.heating_furnace_list[i].set_env(self.start_time, heating_furnace_logs[i])
    #     press_logs = envs['press']
    #     for i in range(len(self.press_list)):
    #         self.press_list[i].set_env(self.start_time, press_logs[i])
    #     cutter_logs = envs['cutter']
    #     for i in range(len(self.cutter_list)):
    #         self.cutter_list[i].set_env(self.start_time, cutter_logs[i])
    #     treatment_furnace_logs = envs['treatment_furnace']
    #     for i in range(len(self.treatment_furnace_list)):
    #         self.treatment_furnace_list[i].set_env(self.start_time, treatment_furnace_logs[i])

    def run(self, simulate_time, day):
        # simulate_time : 몇 일까지 돌아갈지?
        # day : 현재 몇 일째인지?

        if Debug_mode:
            print('- running simulator -')
        # 열처리로 process 등록
        for tf in self.treatment_furnace_list:
            self.env.process(tf.run())
        # self.env.process(self.alloc._recharging())

        simul_end_time = 60 * 24 * simulate_time # N일 후
        self.env.run(until=simul_end_time)

        # 시뮬레이션 결과 정리
        energy = 0
        total_treatment_weight = 0
        logs = []
        for tf in self.treatment_furnace_list:
            energy += tf.total_energy_usage
            total_treatment_weight += tf.total_treatment_weight
            logs.append(tf.log) # 간트차트용 로그, 열처리로가 언제 무엇을 처리했는지 기록
            # penalty_count += self.alloc.penalty_count
        penalty_count = 0
        # update1227 : 마감기한 어기는 penalty 조건 다시 확인 (완)
        for job in self.treatment_job_list:
            if job['properties']['treatment']['next_instruction'] >= len(job['properties']['treatment']['instruction']):
                job['properties']['treatment']['done'] = True

            if job['properties']['treatment']['done']: # 작업 완료라면
                if job['properties']['treatment']['end_time'] > job['properties']['deadline']:
                    # 제때 완료 못했다면
                    penalty_count += 1
            else: # 작업 미완료라면
                if job['properties']['deadline'] < day * 1440:
                    # 마감기한이 시뮬레이션 기간 이내였다면
                    penalty_count += 1
            # if job['properties']['deadline'] <
            # if job['properties']['deadline'] < 1440 * (day + simulate_time) and not job['properties']['treatment']['end_time']:
            #     penalty_count += 1
            # elif job['properties']['treatment']['end_time'] > job['properties']['deadline'] :
            #     penalty_count += 1
            # if job['properties']['deadline'] < 1440 * (day+simulate_time) and not job['properties']['treatment']['done']:
            #
            #     # print(job)
            #     penalty_count += 1

        # print('debug :', total_treatment_weight)
        return energy, total_treatment_weight, penalty_count, logs, self.alloc.furnace_end_time