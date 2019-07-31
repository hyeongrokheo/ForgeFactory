from Simulator.Simulator import *
from copy import deepcopy
from datetime import datetime
import json
from Predictor.Predictor import *
import sys
from RTS import *
from VirtualFactory.V_Simulator import *
#sys.stdout = open('output.txt','w')

"""
todo :

- log 깔끔하게 쓰도록 불필요한것 지우기

- 장비들이 자기 로그 보고 시작상황 세팅하기

- 예측모델 적용 완전히 끝내기

- 커팅하고 제품 개수대로 나뉘게 버그 수정해야함

- 리포트에서 장비별 에너지 -> 총 에너지로 바꿔서 시뮬레이터 끝에 보내주기
총 무게도 전달해야됨 -> 방법 생각해놓기

- 스코어 관련 공식들 더러운 코드 정리

"""

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
    path='./data/190707_test_data/'
    #path = './data/140710_10/'
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


#warnings.filterwarnings(action='ignore')
#from absl import logging
#logging._warn_preinit_stderr = 0

simul_start_time = datetime(2013, 2, 10, 10)
#simul_start_time = datetime(2014, 5, 10, 10)

product_data = read_data('product')
ingot_data = read_data('ingot')
job_data = read_data('job')

sorted(job_data, key=lambda j: j['properties']['order_date'])
new_job_list = []
total_weight = 0
for j in job_data:
    if j['properties']['order_date'] < 0:
        continue
    weight = j['properties']['ingot']['current_weight']
    total_weight += weight
    new_job_list.append(j)
    #print('job :', j)
    if total_weight >= 3000:
        break
print('total weight :', total_weight)
job_data = new_job_list
predictor = Predictor('Planning')
v_predictor = Predictor('Real')

# 휴리스틱 버전으로 24시간 가동
heuristic_simulator = Simulator('Heuristic', predictor, deepcopy(product_data), deepcopy(ingot_data), deepcopy(job_data), 13, 2, 3, 5)
heuristic_simulator.init_simulator()
heuristic_simulator.run(1, save_env=True)
simulator_22envs = deepcopy(heuristic_simulator.envs)
simulator_24envs = deepcopy(heuristic_simulator.envs2)

print('hf 1 log :', simulator_24envs['heating_furnace'][0])
print('hf 2 log :', simulator_24envs['heating_furnace'][1])
print('hf 3 log :', simulator_24envs['heating_furnace'][2])

print('p 1 log :', simulator_24envs['press'][0])
print('p 2 log :', simulator_24envs['press'][1])
print('end heuristic')

# 환경 이어받아 GA 버전으로 가동
ga_simulator = Simulator('GA', predictor, deepcopy(product_data), deepcopy(ingot_data), deepcopy(simulator_22envs['jobs']), 13, 2, 3, 5)
ga = RTS(ga_simulator, deepcopy(simulator_22envs), 1, 1, 1.0, 10.0)
ga_result = ga.run()
log = ga.best_log
print('best log :', log)

#sys.stdout = open('output.txt', 'w')
#print(log['press'][0])

#Debug_mode = True
v_simulator = V_Simulator(v_predictor, deepcopy(product_data), deepcopy(ingot_data), deepcopy(simulator_24envs['jobs']), 13, 2, 3, 5)
v_simulator.set_envs(deepcopy(simulator_24envs))

v_simulator.set_todo(log)
v_simulator.run(2)

print('hf todo :', log['heating_furnace'][0])
print('hf log :', v_simulator.heating_furnace_list[0].log)

print('press todo :', log['press'][0])
print('press log :', v_simulator.press_list[0].log)

#vf_simulator = TestSimulator()
#print('result :', ga_result)




#E, T = simulator.run()
#print('E :', E)
#print('T :', T)
#print()