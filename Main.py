from Simulator.Simulator import *
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
import json
from Predictor.Predictor import *
import sys
from RTS import *
from TreatmentFactory.TreatmentSimulator import *
import plotly.figure_factory as ff

POPULATION = 1
GENERATION = 1
# SIMULATION_MODE = "Heuristic"
SIMULATION_MODE = "GA"

simul_start_time = datetime(2019, 1, 10, 10)

def set_gantt_chart(start_time, log):
    # print('log :', log)
    df = []
    colors = {'treatment_furnace': 'rgb(0, 220, 220)',
              '_treatment_furnace': 'rgb(220, 0, 220)'}

    count = 0
    for tf in log:
        for l in tf:
            if l[1] == 'treatment':
                # print(len(l), l[0], l[1], l[3])
                # if l[4] == 1:
                df.append(dict(State='treatment_furnace', Task='treatment_furnace_' + str(count + 1).zfill(2),
                               Start=start_time + timedelta(minutes=l[0]),
                               Finish=start_time + timedelta(minutes=l[3])))
            elif l[1] == '_treatment':
                # print('123123123')
                # elif l[4] == 2:
                df.append(dict(State='_treatment_furnace', Task='treatment_furnace_' + str(count + 1).zfill(2),
                               Start=start_time + timedelta(minutes=l[0]),
                               Finish=start_time + timedelta(minutes=l[3])))
                # else:
                #     print(l)
        count += 1
    # df = [dict(Task="Job A", Start=start_time + datetime.timedelta(seconds=), Finish=start_time),
    # dict(Task="Job B", Start=start_time, Finish=start_time),
    # dict(Task="Job C", Start=datetime(2014, 5, 10, 10), Finish=datetime(2014, 5, 12, 10))]
    fig = ff.create_gantt(df, colors=colors, index_col='State', group_tasks=True)
    return fig

def get_id_list(obj):
    id_list = []
    for o in obj:
        id_list.append(o['id'])
    return id_list

def dict_to_time(obj):
    return int((datetime(obj['year'], obj['month'], obj['day'], obj['hour'], obj['minute'],
             obj['second'], obj['millisecond'] * 1000) - simul_start_time).total_seconds()/60)

def read(file):
    try:
        with open(file) as fs:
            js = json.load(fs)
            return js
    except Exception as e:
        print("Error: read json", file)
        print(e.message)
        sys.exit(1)

def read_data(file):
    path = './data/140710_10/'
    data = read(path+file+'.json')
    if file == 'product':
        for d in data:
            d['properties']['deadline'] = dict_to_time(d['properties']['deadline'])
            d['properties']['order_date'] = dict_to_time(d['properties']['order_date'])
    elif file == 'job':
        for d in data:
            d['properties']['deadline'] = dict_to_time(d['properties']['deadline'])
            d['properties']['order_date'] = dict_to_time(d['properties']['order_date'])
            d['properties']['current_equip'] = None
            d['properties']['last_process'] = None
            d['properties']['last_process_end_time'] = None
            d['properties']['instruction_list'] = []
            d['properties']['last_heating_furnace'] = None
            d['properties']['next_instruction'] = 0
            d['properties']['product'] = None
            d['properties']['ingot'] = None
            d['access'] = False
            product_id_list = d['properties']['product_id_list']
            for product_id in product_id_list:
                for product in product_data:
                    #print(product['id'], product_id)
                    if product['id'] == product_id:
                        instruction_list = product['properties']['instruction_id_list']
                        if d['properties']['product'] == None:
                            d['properties']['product'] = product['properties']
                        break
                for i in range(len(instruction_list)):
                    inst = instruction_list[i].split('_')
                    if inst[0] == 'heating':
                        instruction_list[i] = 'heating'
                    elif inst[0] == 'forging':
                        instruction_list[i] = 'forging'
                    elif inst[0] == 'cutting':
                        instruction_list[i] = 'cutting'
                    elif inst[0] == 'heat':
                        instruction_list[i] = 'treating'
                        #instruction_list[i] = 'heating'

                d['properties']['instruction_list'].append(instruction_list)
            ingot_id = d['properties']['ingot_id_list'][0]
            if len(d['properties']['instruction_list']) == 0:
                print('Error : instruction list is empty!')
                exit(1)
            for ingot in ingot_data:
                if ingot['id'] == ingot_id:
                    d['properties']['ingot'] = ingot['properties']
                    break
    elif file == 'ingot':
        None
    return data

def read_data_tw(file):
    path = './data/2019_tw/'
    data = read(path+file+'.json')
    # data format
    # "id" : string,
    # "properties" : dictionary
        # "deadline" : datetime dictionary
        # "order_date" : datetime dictionary
        # "current_equip" : string (작업을 현재 처리하고 있는 장비 이름)
        # "last_process" : string (가장 마지막에 진행한 작업, 작업을 시작할 때 기록, 끝난 시점 모름)
        # -> "heating", "forging", "cutting", "treatment"
        # "last_process_end_time" : float (가장 마지막에 진행한 작업이 끝나는 시점, 예측치 입력)
        # "insturction_list" : list [ 원소 "heating", "forging", "cutting", "treating" ]
        # "last_heating_furnace" : string 재장입 위치, 직전 가열했던 가열로에 재장입
        # "next_instruction" : int (last_process 업데이트하면서 같이 업데이트)
        # "product" : 현재 안씀
        # "ingot" : dictionary
            # current_weight : float
            # initail_weight : float
            # "type" : string
        # "treatment" : dictionary (열처리 공정 정보)
            # "instruction" : list [ "Q", "T", "N", "A", "S/R", "S" ]
            # "instruction_temp" : list of list [ min, max ] - 열처리 온도 분류 모형 이용
            # "next_instruction" : int (열처리 공정 시작할 때 업데이트)
            # "preheat" : bool (예열 필요 여부)
            # "done" : bool (열처리 공정 모두 끝났는지 체크)
            # "end_time" : float (가장 마지막에 진행한 열처리 공정이 끝나는 시점, 예측치 입력)
        # "ringmill" : bool (링밀 필요 여부)
        # "chr" : list (열처리 온도 분류 모형 input vector)

    for d in data:
        d['properties']['deadline'] = dict_to_time(d['properties']['deadline'])
        d['properties']['order_date'] = dict_to_time(d['properties']['order_date'])
        d['properties']['current_equip'] = None
        d['properties']['last_process'] = None
        d['properties']['last_process_end_time'] = None
        d['properties']['last_heating_furnace'] = None
        d['properties']['next_instruction'] = 0
        d['properties']['product'] = None
        d['properties']['state'] = None
        d['properties']['treatment']['next_day_not_process'] = False
        d['access'] = False

        if len(d['properties']['instruction_list']) == 0:
            print('Error : instruction list is empty!')
            exit(1)
    return data

# simul_start_time = datetime(2013, 2, 10, 10)


# product_data = read_data('product')
# ingot_data = read_data('ingot')
job_data = read_data_tw('job')
sorted(job_data, key=lambda j: j['properties']['order_date'])

# 주문일자가 limit_day1 일 이전 제거
# 데드라인이 limit_day2 일 이하 제거
# 남은 작업들 new_job_list에 추가, limit_weight 까지 채움

new_job_list = []
total_weight = 0
for j in job_data:
    if j['properties']['order_date'] < -1440 * 14:
        continue
    if j['properties']['deadline'] < 1440 * 7:
        continue
    # print(j)
    weight = j['properties']['ingot']['current_weight']
    total_weight += weight
    new_job_list.append(j)
    #print('job :', j)
    # if total_weight >= 3000:
    #     break
    # if total_weight >= 30000:
    #     break
    if total_weight >= 3000:
        break

print('total weight :', total_weight)
job_data = new_job_list
print('job list :', job_data)
predictor = Predictor('Planning')
v_predictor = Predictor('Real')

# 휴리스틱 버전으로 1일 가동
r_completed_job_list = []
r_treatment_job_list = []
# r_treatment_job_list 구조 : 열처리 공정 대상 작업 목록 + preheat 목록 + tempering 목록
    # 열처리 공정 대상 작업 목록

# 열처리 공정 전까지 휴리스틱 시뮬레이터
# 열처리로 대수는 무조건 1로 설정해야함
# 여기서 열처리로는 작업을 모으고 기다리는 역할
heuristic_simulator = Simulator(predictor, deepcopy(job_data), 13, 2, 3, 1)
heuristic_simulator.init_simulator()
# if SIMULATION_MODE == 'GA':

v_treatment_simulator = TreatmentSimulator(v_predictor, SIMULATION_MODE)
v_treatment_simulator.init_simulator()

# penalty_count_sum = 0
f_energy = 0
f_total_treatment_weight = 0
f_penalty_count = 0

day = 5
last_env = None
for i in range(day):
    # 초기 공장 1일 가동
    print('\nday', i+1, ': heuristic algorithm')

    heuristic_simulator.re_init_simulator() #돌아가던 상태를 유지하면서 초기화
    energy, simulation_time, total_weight, total_heating_weight, treatment_job_list = heuristic_simulator.run(i+1)
    # treatment_job_list : 전단 공정 끝내고 열처리 공정 해야하는 작업 목록 (당일치)
    # r_treatment_job_list : 처리 못한 작업 목록 누적
    r_treatment_job_list.extend(treatment_job_list)
    # print('treatment job id list :', len(treatment_job_list), get_id_list(treatment_job_list))
    # print('r_treatment job id list :', len(r_treatment_job_list), get_id_list(r_treatment_job_list))

    if SIMULATION_MODE == 'GA':
        # GA 열처리로로 하루 가동
        # update::당일 계획에 포함된 작업이 다 끝날 때까지 처리하도록 수정(완) - 넉넉한 일수(7일, RTS의 evaluate에서 상수로 사용 중) 제공
        treatment_simulator = TreatmentSimulator(predictor, 'GA', deepcopy(r_treatment_job_list))
        ga = RTS(treatment_simulator, last_env, r_treatment_job_list, POPULATION, GENERATION, 5.0, 1.0)
        TF_Plan = ga.run(day) # update::계획 당시 현장 상황 반영해서 시뮬레이션 하도록 수정하기(완) - 실제 공장 적용 후 env 가져와서 넣어줌 (last env)
        # TF_Plan : chromosome
        print('\nTF Plan :', TF_Plan)
        job_length = ga.job_length
        preheat_length = ga.preheat_length
        tempering_length = ga.tempering_length

        # 실제공장 열처리로에 하루 가동 - GA결과로
        # re_init_simulator :: chromosome decoder 역할
        v_treatment_simulator.re_init_simulator(r_treatment_job_list, TF_Plan, job_length, preheat_length, tempering_length, last_env=last_env)
        energy, total_treatment_weight, penalty_count, logs, last_env= v_treatment_simulator.run(i+1, day) # i+1
        # print('logs :', logs)

    elif SIMULATION_MODE == 'Heuristic': #update::계획용 predictor를 이용해서 계획한 후 현실 공장에 적용하도록 변경 (완)
        treatment_simulator = TreatmentSimulator(predictor, 'Heuristic', deepcopy(r_treatment_job_list))
        treatment_simulator.init_simulator()
        treatment_simulator.re_init_simulator(r_treatment_job_list, None, None, None, None, last_env=last_env)
        energy, total_treatment_weight, penalty_count, logs, last_env = treatment_simulator.run(7, day+1)
        # TF_Plan : [ [ [ 1호기 작업계획 : [ 1차 열처리 작업 목록], [예열 작업 목록], [ Tempering 작업 목록 ] ], [ 2호기 작업계획], ..., [7호기 작업계획] ] ]
        TF_Plan = treatment_simulator.alloc.furnace_log

        v_treatment_simulator.re_init_simulator(r_treatment_job_list, None, None, None, None, H_TF_Plan = TF_Plan)
        energy, total_treatment_weight, penalty_count, logs, last_env = v_treatment_simulator.run(i+1, day)
        # if energy == 1:
        #     energy = 10000000
    ton_per_energy = total_treatment_weight / energy
    score = ton_per_energy * 100000 + total_treatment_weight - 100 * penalty_count

    f_energy += energy
    f_total_treatment_weight += total_treatment_weight
    f_penalty_count += penalty_count

    r_treatment_job_list = [] # 작업계획 대상 물량
    # update::전날 계획 시 tempering 로가 할당되어 있는 경우는 다음날 작업 계획 대상에서 제거 (완)
    # v_treatment_simulator.alloc.not_process_job_list : 로 할당이 되어있는 작업 목록
    not_process_job_list = v_treatment_simulator.alloc.not_process_job_list # job id list
    for job in v_treatment_simulator.treatment_job_list:
        if job['id'] in not_process_job_list:
            continue
        if job['properties']['treatment']['done']:
            r_completed_job_list.append(job)
        else:
            r_treatment_job_list.append(job)
    print('completed job length :', len(r_completed_job_list))
    print('penalty :', penalty_count)
    print('ton per energy :', ton_per_energy)
    print('total treatment weight :', total_treatment_weight)
    print('score :', score)

# elif SIMULATION_MODE == 'Heuristic':
#     v_treatment_simulator = TreatmentSimulator(v_predictor, 'Heuristic', treatment_job_list)
    # v_treatment_simulator.init_simulator('Real', None, None, None, None)
    # energy, total_treatment_weight, logs = v_treatment_simulator.run(i + 1)

count = 0
completed_job_weight = 0
for job in r_treatment_job_list:
    if job['properties']['deadline'] < 1440 * day:
        # print(job)
        count += 1
for job in r_completed_job_list:
    completed_job_weight += job['properties']['ingot']['current_weight']

print('\nstatistics')
print(SIMULATION_MODE)
print(simul_start_time)
print('energy :', f_energy)
print('weight :', f_total_treatment_weight)
# print('- Work past due date list -')

# gc = set_gantt_chart(simul_start_time, logs)
# gc.show()

print('All Process Completed')
