
furnace_specification = [[120, 10700, 2000, 3490],
                         [150, 13450, 2000, 3490],
                         [200, 11500, 3000, 5200],
                         [200, 11500, 3000, 5600],
                         [200, 11500, 3000, 5600],
                         [120, 10700, 2000, 3490],
                         [150, 16400, 2000, 3490]]
revision = 1  # 테스트용 코드

class TreatmentAllocator:
    def __init__(self, env, type, predictor, treatment_job_list, individual, job_length, preheat_length, tempering_length, last_env):
        self.type = type
        self.env = env
        self.predictor = predictor
        self.treatment_job_list = treatment_job_list

        self.individual = individual
        self.job_length = job_length
        self.preheat_length = preheat_length
        self.tempering_length = tempering_length

        self.penalty_count = 0

        # 열처리로가 결정된 작업 리스트

        # g_allocate_table 에 오늘 처리할 물량 추가
        # update1227 : g_allocate_table 을 보고 예열 및 tempering 안해도 되는 것 계획에서 제외 (완)
        # 예열과 템퍼링 작업 할당할 때 g_allocate_table에 없으면 안하도록 했음
        self.g_allocate_table = []
        self.h_allocate_table = []
        self.t_allocate_table = []

        self.reallocate_preheat_job_list = []
        self.reallocate_table = []

        self.not_process_job_list = []

        self.furnace_log = [[None, None, None], [None, None, None], [None, None, None], [None, None, None],
                            [None, None, None], [None, None, None], [None, None, None]] # type(None) : list. 작업 id 리스트

        if not last_env:
            self.last_furnace_end_time = [0, 0, 0, 0, 0, 0, 0]
        else:
            self.last_furnace_end_time = last_env
            for i in range(len(self.last_furnace_end_time)):
                self.last_furnace_end_time[i] -= 1440
        self.furnace_end_time = [0, 0, 0, 0, 0, 0, 0]

        if self.type == 'GA':
            # self.job_todo : 첫번째 열처리 작업 대상 목록
            self.job_todo = self.treatment_job_list[0:self.job_length]
            # self.preheat_job_todo = self.treatment_job_list[]
            # self.furnace_todo_list : 열처리로별 작업 목록 리스트 (list of list)
            self.furnace_todo_list =[]
            for i in range(7):
                iter = 0  # chromosome gene index
                # print('i :', i)
                # 아래 테스트용 코드
                capacity = furnace_specification[i][0] * revision
                # capacity = furnace_specification[i]
                # print('capacity :', capacity)
                todo_list = []
                treatment_temp_min = None
                treatment_temp_max = None
                while capacity > 0:
                    # print('debug 7')
                    if iter == self.job_length: # 모든 작업을 다 살펴봤으면
                        break
                    # print('iter :', iter)
                    # print('capacity :', capacity)
                    target_job = self.job_todo[individual[iter]]
                    if not self.isAllocatable(furnace_specification[i], target_job):
                        continue
                    if target_job['id'] in self.g_allocate_table: # 이미 열처리로가 결정되어 있으면 패스
                        iter += 1
                        continue

                    if len(todo_list) == 0: # 아직 열처리로에 할당된 작업이 없는 경우
                        todo_list.append(target_job)
                        self.g_allocate_table.append(target_job['id'])
                        weight = target_job['properties']['ingot']['current_weight']
                        treatment_temp = target_job['properties']['treatment']['instruction_temp'][
                            target_job['properties']['treatment']['next_instruction']]
                        treatment_temp_min = treatment_temp[0]
                        treatment_temp_max = treatment_temp[1]
                        capacity -= weight
                        iter += 1
                        continue

                    job_temp = target_job['properties']['treatment']['instruction_temp'][target_job['properties']['treatment']['next_instruction']]
                    job_temp_min = job_temp[0]
                    job_temp_max = job_temp[1]
                    treatment_temp_min2 = treatment_temp_min # new min
                    treatment_temp_max2 = treatment_temp_max # new max
                    if treatment_temp_min < job_temp_min:
                        treatment_temp_min2 = job_temp_min
                    if treatment_temp_max > job_temp_max:
                        treatment_temp_max2 = job_temp_max
                    if treatment_temp_max2 - treatment_temp_min2 < 0:
                        iter += 1
                        continue
                    treatment_temp_min = treatment_temp_min2
                    treatment_temp_max = treatment_temp_max2
                    weight = target_job['properties']['ingot']['current_weight']
                    if capacity >= weight:
                        capacity -= weight
                    else:
                        break
                    todo_list.append(target_job)
                    self.g_allocate_table.append(target_job['id'])
                    iter += 1
                self.furnace_todo_list.append([todo_list, treatment_temp_min])
            self.preheat_job_list = treatment_job_list[self.job_length:self.job_length+self.preheat_length]
            self.preheat_todo_list = individual[self.job_length:self.job_length+self.preheat_length]
            self.tempering_job_list = treatment_job_list[self.job_length+self.preheat_length : self.job_length+self.preheat_length+self.tempering_length]
            self.tempering_todo_list = individual[self.job_length+self.preheat_length : self.job_length+self.preheat_length+self.tempering_length]
            # print('debug a :', len(self.tempering_job_list))
            # print(len(treatment_job_list))
            # print(self.job_length+self.preheat_length, self.job_length+self.preheat_length+self.tempering_length)

            # for tfl in self.furnace_todo_list:
            #     job_list = []
            #     for j in tfl:
            #         job_list.append(j['id'])
                # print(len(job_list), job_list)

    def isAllocatable(self, spec, job):
        # 해당 spec을 갖는 로에 job 을 장입할 수 있는지 확인하는 모듈
        # spec : 로의 스펙 [ 무게, len1, len2, len3 ]
        shape = job['properties']['ingot']['shape']
        size = job['properties']['ingot']['size']
        if shape == 'SQUARE':
            target_size = size[0]
            if target_size < size[1]:
                target_size = size[1]
            if spec[1] > target_size:
                return True
            else:
                return False
        else:
            target_size = size[0]
            if spec[1] > target_size:
                return True
            else:
                return False


    def get_id_list(self, job_list):
        id_list = []
        for job in job_list:
            id_list.append(job['id'])
        return id_list

    def get_job_list(self, id_list):
        job_list = []
        for id in id_list:
            for job in self.treatment_job_list:
                if id == job['id']:
                    job_list.append(job)
                    break
        return job_list

    def predict_treatment_temp(self, job):
        return self.predictor.treatment_temp_prediction(job)

    def get_next_treatment_job(self, num, capacity):
        capacity *= revision
        if self.type == 'GA':
            # target_job_list = []
            # total_weight = 0
            #
            # for i in range(len(self.treatment_job_list)):
            #     job = self.treatment_job_list[i]
            #     if job['properties']['treatment']['done']:
            #         continue
            #     if self.treatment_job_todo[i] == num:
            #         target_job_list.append(job)
            #         # self.treatment_job_todo[i] = -1
            #         total_weight += job['properties']['ingot']['current_weight']
            # if total_weight >= capacity:
            #     self.penalty_count += 1
            total_weight = 0
            for job in self.furnace_todo_list[num][0]:
                total_weight += job['properties']['ingot']['current_weight']
            # print('treatment allocate :', total_weight, '/', capacity)
            return self.furnace_todo_list[num][0], self.furnace_todo_list[num][1]
        elif self.type == 'Heuristic':
            if self.furnace_log[num][0]: # 로그가 있으면 주어진 heuristic 작업 계획대로 실제 공장 가동
                job_list = self.get_job_list(self.furnace_log[num][0])
                return job_list
            else: # 로그가 없으면 heuristic 작업 계획 시스템 가동
                target_job_list = []
                total_weight = 0
                treatment_temp_min = None
                treatment_temp_max = None
                for job in self.treatment_job_list:
                    # if job['properties']['treatment']['end_time'] != 0 and job['properties']['treatment']['end_time'] > self.env.now:
                        # print('debug :', job)
                        # continue
                    if job['id'] in self.h_allocate_table:
                        continue
                    if len(target_job_list) == 0:
                        target_job_list.append(job)
                        self.h_allocate_table.append(job['id'])
                        total_weight += job['properties']['ingot']['current_weight']
                        # treatment_temp = self.predict_treatment_temp(job)
                        treatment_temp = job['properties']['treatment']['instruction_temp'][job['properties']['treatment']['next_instruction']]
                        treatment_temp_min = treatment_temp[0]
                        treatment_temp_max = treatment_temp[1]
                        continue
                    job_temp = job['properties']['treatment']['instruction_temp'][job['properties']['treatment']['next_instruction']]
                    job_temp_min = job_temp[0]
                    job_temp_max = job_temp[1]
                    treatment_temp_min2 = treatment_temp_min
                    treatment_temp_max2 = treatment_temp_max
                    if treatment_temp_min < job_temp_min:
                        treatment_temp_min2 = job_temp_min
                    if treatment_temp_max > job_temp_max:
                        treatment_temp_max2 = job_temp_max
                    if treatment_temp_max2 - treatment_temp_min2 < 0:
                        break
                    treatment_temp_min = treatment_temp_min2
                    treatment_temp_max = treatment_temp_max2
                    if capacity - total_weight >= job['properties']['ingot']['current_weight']:
                        target_job_list.append(job)
                        self.h_allocate_table.append(job['id'])
                        total_weight += job['properties']['ingot']['current_weight']
                        continue
                    else:
                        break
                # print('target job :', capacity, total_weight, target_job_list)
                self.furnace_log[num][0] = self.get_id_list(target_job_list)
                return target_job_list
        else:
            print('allocator type error :', self.type)
            exit(1)

    def reallocate_preheat_job(self, num, preheat_job_list):
        self.reallocate_preheat_job_list.extend(preheat_job_list) #예열로 재배정을 요청하는 순서대로 예열 작업 추가됨
        # num : 열처리로 번호
        self.reallocate_table.append([num, len(preheat_job_list)])

    def allocate_preheat_job(self, num, capacity):
        # update::로 장입 제약사항 추가 (완) - isAllocatable 구현
        if len(self.reallocate_preheat_job_list) == 0:
            return None
        append_job_list = []
        weight = 0
        for job in self.reallocate_preheat_job_list:
            if not self.isAllocatable(furnace_specification[num], job):
                continue
            # print('job :', job)
            if job['properties']['ingot']['current_weight'] < capacity - weight:
                append_job_list.append(job)
                weight += job['properties']['ingot']['current_weight']
                self.reallocate_preheat_job_list.remove(job)
                for i in range(len(self.reallocate_table)):
                    # self.reallocate_table[i][0] : 열처리로 번호
                    # self.reallocate_table[i][1] : 해당 열처리로가 맡긴 예열 작업 개수
                    if self.reallocate_table[i][1] > 0: # 예열 작업 개수가 남아있으면
                        self.reallocate_table[i][1] -= 1
                        break
                # self.reallcate_table[0][1] -= 1
                # if self.reallocate_table[0][0] == 0:
        return append_job_list

    def get_next_preheat_job(self, num, capacity):
        if self.type == 'GA':
            target_job_list = []
            # print(len(self.preheat_job_list), self.preheat_job_list)
            # print(len(self.preheat_job_todo), self.preheat_job_todo)
            for i in range(len(self.preheat_job_list)):
                job = self.preheat_job_list[i]
                if job['id'] in self.g_allocate_table:
                    if num == self.preheat_todo_list[i]:
                        target_job_list.append(job)
            return target_job_list
        elif self.type == 'Heuristic':
            if self.furnace_log[num][1]:
                job_list = self.get_job_list(self.furnace_log[num][1])
                return job_list
            else:
                target_job_list = []
                total_weight = 0
                for job in self.treatment_job_list:
                    if job['properties']['treatment']['end_time'] and job['properties']['treatment']['end_time'] > self.env.now:
                        # 아직 열처리 공정이 진행 중인 작업인 경우 pass
                        continue
                    # 열처리로 capacity 만큼 예열 작업 추가
                    if len(target_job_list) == 0:
                        target_job_list.append(job)
                        total_weight += job['properties']['ingot']['current_weight']
                        continue
                    if capacity - total_weight >= job['properties']['ingot']['current_weight']:
                        target_job_list.append(job)
                        total_weight += job['properties']['ingot']['current_weight']
                        continue
                    else:
                        break
                # print('target job :', capacity, total_weight, target_job_list)
                self.furnace_log[num][1] = self.get_id_list(target_job_list)
                return target_job_list
        else:
            print('allocator type error :', self.type)
            exit(1)

    def get_next_tempering_job(self, num, capacity):
        if self.type == 'GA':
            target_job_list = []
            # print('tempering job list :', self.tempering_job_list)
            for i in range(len(self.tempering_job_list)):
                job = self.tempering_job_list[i]
                # print('job :', job)
                # print(num, self.tempering_todo_list[i])
                if job['id'] in self.g_allocate_table:
                    if num == self.tempering_todo_list[i]:
                        target_job_list.append(job)
            # print('target job list :', len(target_job_list))
            return target_job_list
        elif self.type == 'Heuristic':
            if self.furnace_log[num][2]:
                job_list = self.get_job_list(self.furnace_log[num][2])
                return job_list
            else:
                target_job_list = []
                total_weight = 0
                treatment_temp = 0
                for job in self.treatment_job_list:
                    if job['properties']['treatment']['done']:
                        continue
                    if job['properties']['treatment']['end_time'] and job['properties']['treatment']['end_time'] > self.env.now:
                        continue
                    if job['properties']['treatment']['instruction'][job['properties']['treatment']['next_instruction']] != 'T':
                        continue
                    if job['id'] in self.t_allocate_table:
                        continue
                    if len(target_job_list) == 0:
                        target_job_list.append(job)
                        self.t_allocate_table.append(job['id'])
                        total_weight += job['properties']['ingot']['current_weight']
                        treatment_temp = job['properties']['treatment']['instruction_temp'][
                            job['properties']['treatment']['next_instruction']]
                        treatment_temp_min = treatment_temp[0]
                        treatment_temp_max = treatment_temp[1]
                        continue
                    job_temp = job['properties']['treatment']['instruction_temp'][
                        job['properties']['treatment']['next_instruction']]
                    job_temp_min = job_temp[0]
                    job_temp_max = job_temp[1]
                    treatment_temp_min2 = treatment_temp_min
                    treatment_temp_max2 = treatment_temp_max
                    if treatment_temp_min < job_temp_min:
                        treatment_temp_min2 = job_temp_min
                    if treatment_temp_max > job_temp_max:
                        treatment_temp_max2 = job_temp_max
                    if treatment_temp_max2 - treatment_temp_min2 < 0:
                        continue
                    treatment_temp_min = treatment_temp_min2
                    treatment_temp_max = treatment_temp_max2
                    if capacity - total_weight >= job['properties']['ingot']['current_weight']:
                        target_job_list.append(job)
                        self.t_allocate_table.append(job['id'])
                        # self.allocate_table.append(job['id'])
                        total_weight += job['properties']['ingot']['current_weight']
                        continue
                    else:
                        break
                # print('target job :', capacity, total_weight, target_job_list)
                self.furnace_log[num][2] = self.get_id_list(target_job_list)
                return target_job_list
        else:
            print('allocator type error :', self.type)
            exit(1)