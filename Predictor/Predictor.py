from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from Predictor.DnnRegression import *
from Predictor.OneHotVectorCode import *
from UtilFunction import *
from copy import deepcopy

import random
import os
import pickle
import sklearn

ADD_NOISE = True
# ADD_NOISE = False

def predict_(obj, X):
    from collections import defaultdict
    node_no_list = obj.apply(obj.train_X)
    leaf_node_data_dict = defaultdict(lambda: list())
    leaf_node_dict = dict()
    i = 0
    for _, row in obj.train_X.iterrows():
        leaf_node_data_dict[node_no_list[i]].append(obj.train_y.values[i])
        i += 1

    for key in leaf_node_data_dict.keys():
        leaf_node_dict[key] = {"mean": round(np.mean(leaf_node_data_dict[key]), 2),
                               "var": round(np.var(leaf_node_data_dict[key]), 2),
                               "max": np.max(leaf_node_data_dict[key]),
                               "min": np.min(leaf_node_data_dict[key])}

    predicted_node_list = obj.apply(X)
    # for node in predicted_node_list:
    #     print(node, leaf_node_dict[node])
    # return predicted_node_list, leaf_node_dict
    return leaf_node_dict[predicted_node_list[0]]

class Predictor:
    def __init__(self, type):
        if ADD_NOISE and type == 'Planning':
            print('predictor type : NOISE')
            random.seed(100)
        self.type = type
        # if self.type == 'Planning':
        #     self.model_path = '/ForgeFactory/Predictor/Models/'
        # elif self.type == 'Real':
        #     self.model_path = '/ForgeFactory/Predictor/Models/'
        # self.model_path = '/ForgeFactory/Predictor/Models_VF/'
        # else:
        #     print('Error : predictor type error')
        #     exit(1)
        # self.model_path = './Models/'
        self.model_path = '\\ForgeFactory_TFGA_191230\\Predictor\\Models\\'
        self.project_path = os.path.dirname(os.getcwd())
        # print('debug path :', self.project_path)
        # exit(1)
        # self.project_path = ''

        self.first_heating_time_path = self.model_path + 'first_heating_time'
        self.first_heating_energy_path = self.model_path + 'first_heating_energy'
        self.second_heating_time_path = self.model_path + 'second_heating_time'
        self.second_heating_energy_path = self.model_path + 'second_heating_energy'
        self.maintain_path = self.model_path + 'maintain'
        self.press_path = self.model_path + 'press'
        self.cutting_path = self.model_path + 'cutting'
        self.treatment_time_path = self.model_path + 'treatment_time'
        self.treatment_energy_path = self.model_path + 'treatment_energy'
        # self.treatment_temp_path = './Predictor/Models/treatment_temp.sav'

        self.first_heating_time_model = None
        self.first_heating_energy_model = None
        self.reheating_time_model = None
        self.reheating_energy_model = None
        self.maintain_energy_model = None
        self.forging_time_model = None
        self.cutting_time_model = None
        self.heat_treating_time_model = None
        self.heat_treating_energy_model = None
        self.heat_treating_temp_model = None
        #self.cutting_energy_model = None
        #self.forging_energy_model = None

        self._init_first_heating_time()
        self._init_first_heating_energy()
        self._init_reheating_time()
        self._init_reheating_energy()
        self._init_maintain_energy()
        self._init_forging_time()
        self._init_cutting_time()
        self._init_heat_treating_time()
        self._init_heat_treating_energy()
        # self._init_heat_treating_temp()

        self.door_count = 0

    # def treatment_temp_prediction(self, job):
    #     chr = deepcopy(job['properties']['chr'])
    #     # print('chr :', chr.shape)
    #     # temp = self.heat_treating_temp_model.predict_([chr])
    #     treatment = job['properties']['treatment']['instruction'][job['properties']['treatment']['next_instruction']]
    #     if treatment == 'A':
    #         treatment = 0
    #     elif treatment == 'N':
    #         treatment = 1
    #     elif treatment == 'Q':
    #         treatment = 2
    #     elif treatment == 'S':
    #         treatment = 3
    #     elif treatment == 'S/R':
    #         treatment = 4
    #     elif treatment == 'T':
    #         treatment = 5
    #     else:
    #         print('error : treatment name', treatment)
    #     chr.append(treatment)
    #     # print(chr)
    #     print(1)
    #     info = predict_(self.heat_treating_temp_model, [chr])
    #     print(2)
    #     print('debug data :', chr, info)
    #     # exit(1)
    #     min_temp = info['min']
    #     max_temp = info['max']
    #
    #     return min_temp, max_temp

    # def _init_heat_treating_temp(self):
    #     model = pickle.load(open(self.treatment_temp_path, 'rb'))
    #     self.heat_treating_temp_model = model
    #     # project_path = self.project_path
    #     # model = self.reload_model(self.project_path + self.first_heating_time_path)
    #     # self.first_heating_time_model = model
    #     return True


    # 구현완료
    def heating_time_prediction(self, name, job_list):
        if self.type == 'Planning':
            if len(job_list) == 0:
                print('calc heating time. but job list is empty')
                exit(1)

            total_weight = 0
            max_weight = 0
            for job in job_list:
                w = job['properties']['ingot']['current_weight']
                total_weight += w
                if max_weight < w:
                    max_weight = w
            if total_weight == 0 and max_weight == 0:
                print('Error. weight 0')
                exit(1)

            tmp = [total_weight, max_weight]
            data = furnace_num.TxtToCode(name[-1])
            data.extend(tmp)
            # print(data)
            heating_time = int(self.first_heating_time_model.predict(data)) * 60 # 출력 : 시간(hour)
            if ADD_NOISE and self.type == 'Planning':
                heating_time *= random.gauss(1, 0.125)
                if heating_time < 60:
                    heating_time = 60

            # update1227 : 아래 코드 확인 (완)
            heating_time /= 4
            # print('heating time :', heating_time)
            return heating_time

        elif self.type == 'Real':
            total_weight = 0
            max_weight = 0
            for job in job_list:
                w = job['properties']['ingot']['current_weight']
                total_weight += w
                if max_weight < w:
                    max_weight = w
            if total_weight == 0 and max_weight == 0:
                print('Error. weight 0')
                exit(1)

            #data = furnace_num.TxtToCode(name[-1])
            data = [name[-1]]
            tmp = [total_weight, max_weight]
            data.extend(tmp)
            # print(data)
            heating_time = self.first_heating_time_model.predict(data)
            # print('heating time :', heating_time)
            return heating_time

    # 구현완료
    def reheating_time_prediction(self, name, job_list):
        if len(job_list) == 0:
            print('calc heating time. but job list is empty')
            exit(1)

        total_weight = 0
        max_weight = 0
        for job in job_list:
            w = job['properties']['ingot']['current_weight']
            total_weight += w
            if max_weight < w:
                max_weight = w
        if total_weight == 0 and max_weight == 0:
            return 0

        data = [total_weight, max_weight, len(job_list)]
        reheating_time = int(self.reheating_time_model.predict(data))
        return reheating_time

    def door_manipulate_time(self, equipment, opened=False):
        """
        heating equipment door opening and closing time
        :param equipment: heating equipment entity
        :param opened:
        :return: completion_time (seconds)
        """
        # 처음 5분 추가갯수당 5분

        if opened:
            door_time = 180
            # print("it's opened ", self.door_count,end='')
        else:
            door_time = 300
            self.door_count += 1
            # print("it's open ", self.door_count,end='')
        return door_time

    # 구현완료
    def forging_time_prediction(self, job):
        """weight = job['properties']['ingot']['current_weight']
        if weight <= 15 or weight == None:
            product_size = 'small'
        elif weight <= 25:
            product_size = 'medium'
        else:
            product_size = 'big'

        try:
            product_type = job['properties']['product']['product_type']
        except:
            product_type = 'Cylinder'
        total_round = job['properties']['product']['total_round']
        current_round = job['properties']['product']['current_round']

        data = []
        tmp = press_product_type.TxtToCode(product_type)
        data.extend(tmp)
        tmp = press_product_type.TxtToCode(product_size)
        data.extend(tmp)
        data.append(weight)
        data.append(total_round) # 총 차수
        data.append(current_round) # 현재 차수

        forging_time = int(self.forging_time_model.predict(data) / 60)
        #print('forging_time :', forging_time)
        if ADD_NOISE and self.type == 'Planning':
            forging_time *= random.gauss(1, 0.125)
            if forging_time < 10:
                forging_time = 10"""
        forging_time = 30
        return forging_time

    # 구현완료
    def cutting_time_prediction(self, job):
        # print('job :', job)
        """weight = job['properties']['ingot']['current_weight']
        tmp = cutter_ingot_type.TxtToCode(job['properties']['ingot']['type'])
        prod_count = len(job['properties']['product_id_list'])

        data = [weight]
        data.extend(tmp)
        data.append(prod_count)

        cutting_time = int(self.cutting_time_model.predict(data) / 60)
        if ADD_NOISE and self.type == 'Planning':
            cutting_time *= random.gauss(1, 0.125)
            if cutting_time < 10:
                cutting_time = 10
        #print('cutting time :', cutting_time)"""
        cutting_time = 10
        return cutting_time

    # 구현완료
    # update1227 : 파라미터에 열처리 온도 추가 (완)
    def treatment_time_prediction(self, name, job_list, treatment_temp):
        if len(job_list) == 0:
            return 1
        total_weight = 0

        Q=0
        T=0
        N=0
        A=0
        S=0
        S_R=0
        total_temp = 0
        for job in job_list:
            weight = job['properties']['ingot']['current_weight']
            total_weight += weight
            if job['properties']['treatment']['next_instruction'] >= len(job['properties']['treatment']['instruction']):
                continue
            treatment = job['properties']['treatment']['instruction'][job['properties']['treatment']['next_instruction']]
            if treatment == "Q" and Q == 0:
                Q = 1
            elif treatment == "T" and T == 0:
                T = 1
            elif treatment == "N" and N == 0:
                N = 1
            elif treatment == "A" and A == 0:
                A = 1
            elif treatment == "S" and S == 0:
                S = 1
            elif treatment == "S/R" and S_R == 0:
                S_R = 1
            temp = job['properties']['treatment']['instruction_temp'][job['properties']['treatment']['next_instruction']]
            temp_min = temp[0]
            temp_max = temp[1]
            total_temp += (temp_min + temp_max) / 2
        avg_temp = total_temp / len(job_list)
        # treatment_temp = avg_temp
        # print('treatment temp :', treatment_temp)
        holding_time = 8 # 다시짜야됨. 홀딩시간 기준 새로 정해서
        # print('total_weight :', total_weight)
        if not treatment_temp:
            treatment_temp = avg_temp
        n_treatment_temp = abs(treatment_temp - 893.125) / 35.12
        n_holding_time = abs(holding_time - 6.625) / 1.849
        n_total_weight = abs(total_weight - 116.165) / 25.528
        data = [n_treatment_temp, n_holding_time, n_total_weight, Q, T, N, A, S, S_R]
        treatment_time = self.heat_treating_time_model.predict(data) / 60
        # print('treatment time :', treatment_time)

        if ADD_NOISE and self.type == 'Real':
            treatment_time *= random.gauss(1, 0.125)
            if treatment_time < 420: # 7시간보다 짧으면 이상한 상황. upperbound 도 추가 필요함.
                treatment_time = 420

        return int(treatment_time)

    # def treatment_cooling_time_prediction(self, equipment, parameter=None):
    #     """
    #
    #     :param equipment: treatment equipment entity
    #     :param parameter:
    #     :return: completion_time (seconds)
    #     """
    #     # 6시간
    #     treat_time = 64800
    #     treat_time += random.gauss(0, 1) * 3600
    #     return treat_time  # random.randint(10, 15)
    #
    # def convey_time_prediction(self, job):
    #     """
    #     이동시간 현재 3분,,,
    #     :param current: current equipment
    #     :param next: next equipment
    #     :return: complete time (seconds)
    #     """
    #
    #     return 180  # random.randint(60, 90)

    # 구현완료
    def heating_energy_prediction(self, name, job_list, heating_time):
        total_weight = 0
        max_weight = 0
        job_id_list = []
        for j in job_list:
            job_id_list.append(j['id'])
            weight = j['properties']['ingot']['current_weight']
            total_weight += weight
            if max_weight < weight:
                max_weight = weight
        data = furnace_num.TxtToCode(name[-1])
        tmp = [heating_time, total_weight, max_weight]
        data.extend(tmp)
        heating_energy = self.first_heating_energy_model.predict(data)
        if ADD_NOISE and self.type == 'Planning':
            heating_energy *= random.gauss(1, 0.125)
            if heating_energy < 500:
                heating_energy = 500

        # print('job list :', job_id_list)
        # print('heating energy :', heating_energy)
        return heating_energy

    # 구현완료
    def reheating_energy_prediction(self, job_list, heating_time):
        total_weight = 0
        max_weight = 0
        for j in job_list:
            weight = j['properties']['ingot']['current_weight']
            total_weight += weight
            if max_weight < weight:
                max_weight = weight
        data = [heating_time, total_weight, max_weight, len(job_list)]
        reheating_energy = self.reheating_energy_model.predict(data)
        return reheating_energy

    def cal_door_manipulate_energy_usage(self, manipulate_time=None):
        """
        if door open, need to heating
        :param equipment:
        :param manipulate_time:
        :return:
        """
        # 시간당 600
        # 분당 10
        if manipulate_time is None:
            manipulate_time = 300
        door_energy_usage = (manipulate_time / 3600) * 800
        return door_energy_usage

    def cal_maintain_energy_usage(self, equipment, total_weight=None, max_weight=None, time=None):
        """
        if heating equipment do nothing, spend energy to maintain the internal temperature
        :param equipment: heating equipment
        :param time:
        :return: energy_usage
        """
        if time is None:
            maintain_energy_usage = (284.514 - 1.043) * 0.01
            return maintain_energy_usage
        if max_weight is None:
            maintain_energy_usage = (284.514 - 1.043) * (time / 3600)
        else:
            # maintain_energy_usage = (284.514 - (1.043 * max_weight)) * (time / 3600)
            tmp = furnace_num.TxtToCode(equipment.id[-1])
            data = tmp + [time / 3600, total_weight, max_weight, len(equipment.job_id_list())]

            maintain_energy_usage = self.maintain_energy_model.predict(data)

        return maintain_energy_usage

    # 구현완료
    def forging_energy_prediction(self, time=None):
        """

        :param equipment: heating equipment
        :param time: how long use the equipment
        :return: energy_usage
        """

        if time is None:
            print('Error : cutting time is not exist')
            exit(0)

        forging_energy = time * 200
        return forging_energy

    # 구현완료
    def cutting_energy_prediction(self, time=None):
        """

        :param equipment: heating equipment
        :param time: how long use the equipment
        :return: energy_usage (KW)
        """
        cutting_energy = time * 200
        return cutting_energy

    # update1227 : 파라미터에 열처리 온도 추가 (완)
    def treatment_energy_prediction(self, name, job_list, treatment_time, treatment_temp):
        if len(job_list) == 0:
            return 0
        total_weight = 0

        Q = 0
        T = 0
        N = 0
        A = 0
        S = 0
        S_R = 0
        total_temp = 0
        for job in job_list:
            weight = job['properties']['ingot']['current_weight']
            total_weight += weight
            if job['properties']['treatment']['next_instruction'] >= len(job['properties']['treatment']['instruction']):
                continue
            treatment = job['properties']['treatment']['instruction'][job['properties']['treatment']['next_instruction']]
            if treatment == "Q" and Q == 0:
                Q = 1
            elif treatment == "T" and T == 0:
                T = 1
            elif treatment == "N" and N == 0:
                N = 1
            elif treatment == "A" and A == 0:
                A = 1
            elif treatment == "S" and S == 0:
                S = 1
            elif treatment == "S/R" and S_R == 0:
                S_R = 1
            temp = job['properties']['treatment']['instruction_temp'][
                job['properties']['treatment']['next_instruction']]
            temp_min = temp[0]
            temp_max = temp[1]
            total_temp += (temp_min + temp_max) / 2
        avg_temp = total_temp / len(job_list)
        # treatment_temp = avg_temp

        # treatment_temp = 800
        holding_time = 8  # 다시짜야됨. 홀딩시간 기준 새로 정해서
        # print('total_weight :', total_weight)
        if not treatment_temp:
            treatment_temp = avg_temp
        n_treatment_temp = abs(treatment_temp - 893.125) / 35.12
        n_holding_time = abs(holding_time - 6.625) / 1.849
        n_total_weight = abs(total_weight - 116.165) / 25.528
        data = [n_treatment_temp, n_holding_time, n_total_weight, Q, T, N, A, S, S_R]

        # update1227 : heat_treating_time_model 이 아니라 energy 써야하는데... 확인! (완)
        treatment_energy = self.heat_treating_energy_model.predict(data)

        if ADD_NOISE and self.type == 'Real':
            treatment_energy *= abs(random.gauss(1, 0.125))

        return treatment_energy

    def _heating_time_prediction(self, dataset):
        # dataset = Data.dict_to_dataset(feature, 0)

        y = self.first_heating_time_model.predict(dataset)

        return y

    def _heating_energy_prediction(self, dataset):
        # dataset = Data.dict_to_dataset(feature, 0)
        y = self.first_heating_energy_model.predict(dataset)
        return y

    def _maintain_energy_prediction(self, dataset):
        # dataset = Data.dict_to_dataset(feature, 0)
        y = self.maintain_energy_model.predict(dataset)
        return y

    def _cutting_time_prediction(self, dataset):
        # dataset = Data.dict_to_dataset(feature, 0)
        y = self.cutting_time_model.predict(dataset)
        return y

    def _forging_time_prediction(self, dataset):
        y = self.forging_time_model.predict(dataset)
        return y

    def _reheating_time_prediction(self, dataset):
        y = self.reheating_time_model.predict(dataset)
        return y

    def _reheating_energy_prediction(self, dataset):
        y = self.reheating_energy_model.predict(dataset)
        return y

    def _heat_treating_time_prediction(self, dataset):
        y = self.heat_treating_time_model.predict(dataset)
        return y

    def _heat_treating_energy_prediction(self, dataset):
        y = self.heat_treating_energy_model.predict(dataset)
        return y

    def _init_first_heating_time(self):
        #project_path = self.project_path
        model = self.reload_model(self.project_path + self.first_heating_time_path)
        self.first_heating_time_model = model
        return True

    def _init_first_heating_energy(self):
        project_path = self.project_path
        model_fn = project_path + self.first_heating_energy_path
        model = self.reload_model(model_fn)
        self.first_heating_energy_model = model
        return True

    def _init_maintain_energy(self):

        project_path = self.project_path
        model_fn = project_path + self.maintain_path
        model = self.reload_model(model_fn)
        self.maintain_energy_model = model

        return True

    def _init_reheating_time(self):
        project_path = self.project_path

        model_fn = project_path + self.second_heating_time_path
        model = self.reload_model(model_fn)

        self.reheating_time_model = model
        return True

    def _init_reheating_energy(self):
        project_path = self.project_path
        model_fn = project_path + self.second_heating_energy_path
        model = self.reload_model(model_fn)

        self.reheating_energy_model = model
        return True

    def _init_cutting_time(self):
        project_path = self.project_path
        model_fn = project_path + self.cutting_path
        model = self.reload_model(model_fn)
        self.cutting_time_model = model
        return True

    def _init_forging_time(self):
        project_path = self.project_path
        model_fn = project_path + self.press_path
        model = self.reload_model(model_fn)

        self.forging_time_model = model
        return True

    def _init_heat_treating_time(self):
        project_path = self.project_path

        model_fn = project_path + self.treatment_time_path
        model = self.reload_model(model_fn)

        self.heat_treating_time_model = model
        return True

    def _init_heat_treating_energy(self):
        project_path = self.project_path

        model_fn = project_path + self.treatment_energy_path
        model = self.reload_model(model_fn)

        self.heat_treating_energy_model = model
        return True

    def reload_model(self, model_fn):
        model = DnnRegression()
        model.load(model_fn)
        return model

    def print_count(self):
        print('first_heating_time ', self.first_heating_time_model.count)
        print('first_heating_energy ', self.first_heating_energy_model.count)
        print('maintain_energy ', self.maintain_energy_model.count)

        print('reheating_time ', self.reheating_time_model.count)
        print('reheating_energy ', self.reheating_energy_model.count)

        print('cutting_time ', self.cutting_time_model.count)

        print('forging_time ', self.forging_time_model.count)

        print('heat_treating ', self.heat_treating_time_model.count)
        print('heat_treating_energy ', self.heat_treating_energy_model.count)
