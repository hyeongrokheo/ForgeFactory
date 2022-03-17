def get_id_list(obj):
    id_list = []
    for o in obj:
        id_list.append([o['id'], o['properties']['ingot']['current_weight']])
    return id_list

class TreatmentFurnace:
    def __init__(self, env, allocator, spec, num):
        self.env = env
        self.alloc = allocator

        self.num = num
        self.name = 'treatment_furnace_' + str(num + 1)
        self.capacity = spec[0]
        self.length = spec[1]
        self.width = spec[2]
        self.height = spec[3]

        self.total_treatment_weight = 0
        self.total_energy_usage = 0
        self.total_preheat_weight = 0

        self.log = []

    def set_alloc(self, alloc):
        self.alloc = alloc

    def get_id_list(self, job_list):
        id_list = []
        for job in job_list:
            id_list.append(job['id'])
        return id_list

    def calc_treatment_time(self, treatment_job_list, treatment_temp):
        treatment_time = self.alloc.predictor.treatment_time_prediction(self.name, treatment_job_list, treatment_temp)
        return treatment_time

    def calc_treatment_energy(self, treatment_job_list, treatment_time, treatment_temp):
        treatment_energy = self.alloc.predictor.treatment_energy_prediction(self.name, treatment_job_list, treatment_time, treatment_temp)
        return treatment_energy

    def append_preheat_job(self, capacity):
        return self.alloc.allocate_preheat_job(self.num, capacity)

    def reallocate_preheat_job(self, num, preheat_job_list):
        self.alloc.reallocate_preheat_job(num, preheat_job_list)

    def write_log(self, current_time, state, treatment_job_list, treatment_end_time):
        # state = ['treatment', '_treatment'] , 추후 예열 넣으면 됨.
        # if treatment_num == 1:
        self.log.append([current_time, state, treatment_job_list, treatment_end_time])
        # elif treatment_num == 2:
        #     self.log.append([current_time, 'treatment', treatment_job_list, treatment_end_time])

    def run(self):
        while True:
            # 열처리로 병렬 처리 시 에러 해결하기 위한 방법
            # 시뮬레이션 처음 시작할 때만 발생하는 문제
            # 열처리로 번호에 해당하는 *0.1분만큼 지나서 동작 시작하도록 처리함
            yield self.env.timeout(self.num * 0.1)

            # 전날 공정이 끝날 때까지 기다림
            preprocess = self.alloc.last_furnace_end_time[self.num]
            if preprocess > 0:
                yield self.env.timeout(self.alloc.last_furnace_end_time[self.num])

            treatment_job_list, treatment_temp = self.alloc.get_next_treatment_job(self.num, self.capacity)
            tempering_job_list = self.alloc.get_next_tempering_job(self.num, self.capacity)
            self.alloc.not_process_job_list.extend(self.get_id_list(tempering_job_list))
            # print(self.env.now, self.name, 'treatment job list :', len(get_id_list(treatment_job_list)), get_id_list(treatment_job_list))
            if len(treatment_job_list) == 0:
                # print('treatment job list is empty!')
                # yield self.env.timeout(30)
                # update::남은 하루를 보내기 (완)
                now = self.env.now
                while now >= 0:
                    now -= 1440
                now += 1440
                now = 1440 - now
                yield self.env.timeout(now)
                # exit(1)

            treatment_time = self.calc_treatment_time(treatment_job_list, treatment_temp)
            treatment_energy = self.calc_treatment_energy(treatment_job_list, treatment_time, treatment_temp)
            # treatment_time = 1000 # 임시로 해둠. 추후 받아오는 데이터 추가해서 모델 활용
            # treatment_energy = 1000 # 임시로 해둠. 추후 받아오는 데이터 추가해서 모델 활용

            for j in treatment_job_list:
                self.total_treatment_weight += j['properties']['ingot']['current_weight']
            self.total_energy_usage += treatment_energy
            # print(self.name, treatment_time, treatment_energy)
            self.write_log(self.env.now, 'treatment', treatment_job_list, self.env.now+treatment_time)
            # end_time 써주고 시간 흘리기
            # 아니면 시간 흐르는 사이에 다른 열처리로가 가져갈 수 있음
            # 순서 중요!!
            for job in treatment_job_list:
                job['properties']['treatment']['end_time'] = self.env.now + treatment_time
                job['properties']['treatment']['next_instruction'] += 1
                # 전체 공정 끝난 작업이면 'done'
                if len(job['properties']['treatment']['instruction']) == job['properties']['treatment']['next_instruction']:
                    job['properties']['treatment']['done'] = True
            self.alloc.furnace_end_time[self.num] = self.env.now + treatment_time
            yield self.env.timeout(treatment_time)

            preheat_job_list = self.alloc.get_next_preheat_job(self.num, self.capacity)
            preheat_job_weight = 0
            for job in preheat_job_list:
                preheat_job_weight += job['properties']['ingot']['current_weight']

            # update1227 : not_process_job_list 에 넣어주는 시점 더 위로 가야할 듯? (완)

            # tempering 작업 목록이 모두 준비되었는지 체크
            while True:
                # print('in while')
                # print('tempering job list :', tempering_job_list)
                new_preheat_job = self.append_preheat_job(self.capacity - preheat_job_weight)
                if new_preheat_job:
                    self.alloc.not_process_job_list.extend(self.get_id_list(new_preheat_job))
                    preheat_job_list.extend(new_preheat_job)

                yield self.env.timeout(10)
                # print(1)
                # 내가 처리해야할 tempering 작업이 모두 모였는지 확인
                tempering_start = True
                for job in tempering_job_list:
                    # print(self.env.now, job['properties']['treatment']['end_time'])
                    if self.env.now < job['properties']['treatment']['end_time']: # 아직 첫번째 열처리공정이 안끝난 작업이 있으면
                        tempering_start = False
                        break
                # update::아래 로직 이상함!! 확인 필요 (완)
                if tempering_start:
                    break

            # update::tempering 시작 전 실제 처리 예열량 계산 구현하기 (완)
            # update::내가 지금 처리 중인 예열 작업들이 다른 로에 모두 할당이 됐는지 체크! (완)
            # 예열로 재배정이 모두 끝났는지 확인
            self.reallocate_preheat_job(self.num, preheat_job_list)
            tempering_start2 = False
            while True:
                # print('debug azzz')
                for i in range(len(self.alloc.reallocate_table)):
                    if self.alloc.reallocate_table[i][0] == self.num and self.alloc.reallocate_table[i][1] == 0:
                        # 해당 열처리로가 맡긴 예열 작업 중 재할당이 필요한 작업 개수가 0개 이면 예열로 재배정이 끝났음
                        # tempering 작업 시작!
                        self.alloc.reallocate_table.remove(self.alloc.reallocate_table[i])
                        tempering_start2 = True
                        # print('debug asss')
                        break
                if tempering_start2:
                    break
                yield self.env.timeout(30) # 30분 후 재확인

            # 내가 실제로 처리한 예열 작업 무게 계산
            for job in preheat_job_list:
                weight = job['properties']['ingot']['current_weight']
                # update1227 : 로직 다시 확인. (완)
                # 제품 생산 진행 중이고
                # 다음 작업이 tempering이 아니고
                # 현재 처리 중인 공정이 진행 중이면
                if job['properties']['treatment']['next_instruction'] >= len(job['properties']['treatment']['instruction']):
                    continue
                if self.env.now < job['properties']['treatment']['end_time']: # 끝나는 시간이 미래 = 작업중
                    continue
                if job['properties']['treatment']['instruction'][job['properties']['treatment']['next_instruction']] == 'T':
                    # 끝나는 시간이 과거인 경우에만. 현재 진행중 작업이 끝나고 다음 할 작업이 T인 경우라면 -> 아직 예열로로 진입하지 않았음
                    continue

                self.total_preheat_weight += weight

            tempering_time = self.calc_treatment_time(tempering_job_list, None)
            tempering_energy = self.calc_treatment_energy(tempering_job_list, tempering_time, None)
            self.total_energy_usage += tempering_energy
            # treatment : 첫번째 열처리 공정인 경우 (tempering 포함 될 수 있음)
            # _treatment : 두번째 열처리 공정인 경우 (tempering)
            self.write_log(self.env.now, '_treatment', treatment_job_list, self.env.now + tempering_time)
            # print('123123123')
            for job in tempering_job_list:
                job['properties']['treatment']['end_time'] = self.env.now + tempering_time
                job['properties']['treatment']['next_instruction'] += 1
                # 전체 공정 끝난 작업이면 'done'
                if len(job['properties']['treatment']['instruction']) == job['properties']['treatment']['next_instruction']:
                    job['properties']['treatment']['done'] = True
            self.alloc.furnace_end_time[self.num] = self.env.now + tempering_time
            yield self.env.timeout(tempering_time)
            for job in tempering_job_list:
                job_id = job['id']
                if job_id in self.alloc.not_process_job_list:
                    self.alloc.not_process_job_list.remove(job_id)

            # update::로직 체크!! (완)
            now = self.env.now
            while now >= 0:
                now -= 1440
            now += 1440
            now = 1440 - now
            yield self.env.timeout(now)