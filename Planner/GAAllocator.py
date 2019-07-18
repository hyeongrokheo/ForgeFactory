from Equipment.HeatingFurnace import *
from queue import Queue
import time
class GAAllocator:
    def __init__(self, env, predictor, heating_furnace_num, job, individual):
        self.env = env
        self.predictor = predictor
        self.heating_furnace_num = heating_furnace_num
        self.insertion = self.env.event()
        self.request = self.env.event()

        self.job = sorted(job, key=lambda j: j['properties']['deadline'])
        self.hf_list = individual

        self.discharging_wakeup = []
        self.recharging_wakeup = []
        for i in range(heating_furnace_num):
            self.discharging_wakeup.append(simpy.Store(self.env))
            self.recharging_wakeup.append(simpy.Store(self.env))
        self.waiting_job = []
        self.complete_job = []
        self.recharging_queue = []

        self.simulate_end_time = 0

        self.hf_count = 0

    def end_simulator(self):
        for j in self.job:
            if j['properties']['state'] != 'done':
                return False
        return True

    def next_job_list(self, process):
        next_job = []
        for job in self.job:
            if job['properties']['last_process'] != 'holding':
                continue
            if job['properties']['state'] == 'done':
                continue
            if (job['properties']['last_process_end_time'] < self.env.now) and (job['properties']['instruction_list'][0][job['properties']['next_instruction']] == process):
                #print('debug2 : ', self.env.now, job)
                next_job.append(job)
        #print('debug : wj :', self.waiting_job)
        for wj in self.waiting_job:
            #구문 remove 필요
            if wj['properties']['state'] == 'done':
                continue
            if wj['properties']['last_process_end_time'] > self.env.now:
                self.waiting_job.remove(wj)
                continue
            if wj['properties']['instruction_list'][0][wj['properties']['next_instruction']] == process:
                next_job.append(wj)
                #self.waiting_job.remove(wj)

        #print('debug : nj :', next_job)
        return next_job

    def job_update(self, job, equip_name, process_name, last_heating_furnace_name=None):
        # 세영수정
        job['properties']['current_equip'] = equip_name
        job['properties']['last_process'] = process_name
        if last_heating_furnace_name != None:
            job['properties']['last_heating_furnace'] = last_heating_furnace_name
        job['properties']['next_instruction'] += 1
        if len(job['properties']['instruction_list']) == job['properties']['next_instruction']:
            job['properties']['state'] = 'done'
            self.simulate_end_time = self.env.now

    def is_allocated_to_heating_furnace(self, j, furnace_name):
        # 세영수정
        # 가열로에 할당된 작업인지 확인
        if j['properties']['current_equip'] != None and j['properties']['current_equip'] == furnace_name:
            return True
        return False

    def select_job_for_heating_furnace(self, src_job, candidate_job_list, furnace_name):
        # 세영수정
        # 후보 작업 목록 중 src_job 과 1) 무게가 같고 2) 마감기한 간격이 7일 이내인 작업만 선택
        src_job_weight = src_job['properties']['ingot']['current_weight']
        src_job_deadline = src_job['properties']['deadline']
        alloc_deadline_limit = src_job_deadline + 7 * 24 * 60
        selected_job_list = []
        for j in candidate_job_list:
            if self.is_allocated_to_heating_furnace(j, furnace_name):
                continue
            cur_job_deadline = j['properties']['deadline']
            cur_job_weight = j['properties']['ingot']['current_weight']
            if cur_job_deadline < alloc_deadline_limit and cur_job_weight == src_job_weight:
                selected_job_list.append(j)
        return selected_job_list

    def heating_allocate(self, name, num, capacity):
        allocate_job_list = []
        print('name :', name)
        print('num :', num)
        print('capacity :', capacity)
        exit(1)
        total_weight = 0
        while True:
            candidate_job_num = None
            try:
                candidate_job_num = self.individual.index(num)
                self.individual[candidate_job_num] = -1
            except:
                None

            if candidate_job_num != None:
                job = self.job[candidate_job_num]
                weight = job['properties']['ingot']['current_weight']

                if total_weight + weight <= capacity:
                    total_weight += weight
                    allocate_job_list.append(job)
                else:
                    break
            else:
                break

        for j in allocate_job_list:
            self.job_update(j, name, 'heating', name)
        print('alloc job list :', allocate_job_list)
        exit(1)
        return allocate_job_list
        # -----------------------------------------------------------------------
        # 가열로 작업 할당 휴리스틱
        # 1. 마감기한이 가장 이른 작업 하나 선택
        # 2. 마감기한 간격 7일 내 해당 작업과 동일 제품 혹은 동일 무게 작업 선택
        # 3. 가열로 Capacity 85% 이상 채워질 때까지 반복
        # -----------------------------------------------------------------------

        # 후보 작업 목록
        # candidate_job_list = []
        # for j in self.job:
        #     if j['properties']['state'] == 'done':
        #         continue
        #
        #     last_process_end_time = j['properties']['last_process_end_time']
        #     try:
        #         # 예외처리보완필요
        #         # treating 중인 작업들의 경우 len(j['properties']['instruction_list']) == j['properties']['next_instruction'] 인 경우 발생
        #         # list index out of range 에러 발생
        #         next_instruction = j['properties']['instruction_list'][0][j['properties']['next_instruction']]
        #     except:
        #         pass
        #     if last_process_end_time == None and next_instruction == 'heating':
        #         candidate_job_list.append(j)
        #     if last_process_end_time != None and last_process_end_time < self.env.now and next_instruction == 'heating':
        #         candidate_job_list.append(j)
        # if len(candidate_job_list) == 0:
        #     return None
        #
        # allocate_job_list = []
        # total_weight = 0
        #
        # candidate_job_list = sorted(candidate_job_list, key=lambda j: j['properties']['deadline'])
        # for urgent_job in candidate_job_list:
        #     urgent_job_weight = urgent_job['properties']['ingot']['current_weight']
        #     if self.is_allocated_to_heating_furnace(j, name):
        #         continue
        #     if total_weight + urgent_job_weight > capacity:
        #         continue
        #
        #     allocate_job_list.append(urgent_job)
        #     total_weight += urgent_job_weight
        #     self.job_update(urgent_job, name, 'heating')
        #
        #     selected_job_list = self.select_job_for_heating_furnace(urgent_job, candidate_job_list, name)
        #     for candidate_job in selected_job_list:
        #         candidate_job_weight = candidate_job['properties']['ingot']['current_weight']
        #         if total_weight + candidate_job_weight > capacity:
        #             continue
        #         allocate_job_list.append(candidate_job)
        #         total_weight += candidate_job_weight
        #         self.job_update(candidate_job, name, 'heating', name)



    def recharging(self, job):
        self.recharging_queue.append(job)

    def _recharging(self):
        while True:
            if len(self.recharging_queue) != 0:
                self.recharging_wakeup[self.hf_count].put(self.recharging_queue[0])
            yield self.env.timeout(1)
            self.hf_count += 1
            if self.hf_count == self.heating_furnace_num:
                self.hf_count = 0

    def get_next_press_job(self, name):
        candidate_job_list = self.next_job_list('forging')
        if len(candidate_job_list) == 0:
            return None
        if Debug_mode:
            print('후보 작업들은')
            nPrint(candidate_job_list)
        candidate_job_list = sorted(candidate_job_list, key=lambda j: j['properties']['deadline'])
        target_job = candidate_job_list[0]
        if target_job['properties']['last_process'] == 'holding':
            for i in range(self.heating_furnace_num):
                self.discharging_wakeup[i].put([target_job['properties']['last_heating_furnace'], target_job])
        #print(self.env.now, 'press target job :', target_job)
        self.job_update(job=target_job, equip_name=name, process_name='press')
        if Debug_mode:
            print(self.env.now, 'press target job :')
            nPrint(target_job)

        index = None
        try:
            index = self.waiting_job.index(target_job)
        except:
            None
        if index != None:
            self.waiting_job.remove(target_job)

        return target_job

    def get_next_cut_job(self, name):
        candidate_job_list = self.next_job_list('cutting')
        if len(candidate_job_list) == 0:
            return None
        candidate_job_list = sorted(candidate_job_list, key=lambda j: j['properties']['deadline'])
        target_job = candidate_job_list[0]
        if target_job['properties']['last_process'] == 'holding':
            for i in range(self.heating_furnace_num):
                self.discharging_wakeup[i].put([target_job['properties']['last_heating_furnace'], target_job])
        self.job_update(job=target_job, equip_name=name, process_name='cut')
        if Debug_mode:
            print(self.env.now, 'cutter target job :')
            nPrint(target_job)

        index = None
        try:
            index = self.waiting_job.index(target_job)
        except:
            None
        if index != None:
            self.waiting_job.remove(target_job)

        return target_job

    def end_job(self, job):
        if len(job['properties']['instruction_list'][0]) == job['properties']['next_instruction']:
            job['properties']['state'] = 'done'
            self.simulate_end_time = self.env.now
            self.complete_job.append(job)
        elif job['properties']['instruction_list'][0][job['properties']['next_instruction']] == 'heating':
            self.recharging(job)
        else:
            self.waiting_job.append(job)

    def get_next_treatment_job(self, name, capacity):
        # ----------------------------------------------------------------------------------------------------
        # 열처리로 작업 할당 휴리스틱
        # 1. 마감기한이 임박한 순으로 작업 선택
        # 2. 열처리로 Capacity 85% 이상 채워질 때까지 대기 - 현재는 70%
        # 3. 열처리 공정 소요 시간을 예측했을 때 마감기한을 어기는 작업이 생길 경우 더이상 기다리지 않고 할당
        # ----------------------------------------------------------------------------------------------------
        candidate_job_list = []
        for j in self.job:
            if j['properties']['state'] == 'done':
                #완료된 작업
                continue
            if j['properties']['last_process_end_time'] != None and j['properties']['last_process_end_time'] > self.env.now:
                #다른 작업 진행중
                continue
            #print('debug :', j['id'], j['properties']['instruction_list'][0], j['properties']['next_instruction'])
            if j['properties']['instruction_list'][0][j['properties']['next_instruction']] == 'treating':
                candidate_job_list.append(j)

        if len(candidate_job_list) == 0:
            return None

        candidate_job_list = sorted(candidate_job_list, key=lambda j: j['properties']['deadline'])
        standard_deadline = candidate_job_list[0]['properties']['deadline']
        target_job_list = []
        total_weight = 0
        if Debug_mode:
            print('cjl')
            nPrint(candidate_job_list)

        for j in candidate_job_list:
            cur_job_weight = j['properties']['ingot']['current_weight']
            total_weight += cur_job_weight
            target_job_list.append(j)
            treatment_time = self.predictor.treatment_time_prediction(name, target_job_list)

            if self.env.now + treatment_time < standard_deadline and total_weight < capacity:
                if self.env.now + treatment_time + 30 >= standard_deadline:
                    break
                elif total_weight >= capacity * 0.85:
                    break
                else:
                    continue
            else:
                total_weight -= cur_job_weight
                target_job_list.remove(j)
                break
        for j in target_job_list:
            j['properties']['current_equip'] = name
            j['properties']['last_process'] = 'treatment'
            j['properties']['next_instruction'] += 1
        return target_job_list



            #추가여부 결정
        #     if total_weight < capacity:
        #
        #         treatment_time = self.predictor.treatment_time_prediction(name, target_job_list)
        #         if Debug_mode:
        #             print('-')
        #             nPrint(target_job_list)
        #             print('current time :', self.env.now)
        #             print('treatment time :', treatment_time)
        #             print('deadline :', standard_deadline)
        #
        #         if self.env.now + treatment_time + 30 < standard_deadline:
        #
        #         else:
        #             if self.env.now + treatment_time <= standard_deadline:
        #                 total_weight += cur_job_weight
        #                 return target_job_list
        #             else:
        #                 target_job_list.remove(j)
        #                 if len(target_job_list) == 0:
        #                     return None
        #                 for j in target_job_list:
        #                     j['properties']['current_equip'] = name
        #                     j['properties']['last_process'] = 'treatment'
        #                     j['properties']['next_instruction'] += 1
        #                 return target_job_list
        #
        #         total_weight += cur_job_weight
        #     else:
        #         for j in target_job_list:
        #             j['properties']['current_equip'] = name
        #             j['properties']['last_process'] = 'treatment'
        #             j['properties']['next_instruction'] += 1
        #         return target_job_list
        # #print('debug : cjl :', candidate_job_list)
        # if total_weight > capacity * 0.7:
        #     for j in target_job_list:
        #         j['properties']['current_equip'] = name
        #         j['properties']['last_process'] = 'treatment'
        #         j['properties']['next_instruction'] += 1
        #     return target_job_list
        # return None

        #
        # for j in target_job_list:
        #     j['properties']['current_equip'] = name
        #     j['properties']['last_process'] = 'treatment'
        #     j['properties']['next_instruction'] += 1
        #
        # return target_job_list