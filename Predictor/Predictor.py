from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from Predictor.DnnRegression import *
from Predictor.OneHotVectorCode import *
from UtilFunction import *

import random
import os

class Predictor:
    def __init__(self):
        self.model_path = '/ForgeFactory/Predictor/Models/'
        self.project_path = os.path.dirname(os.getcwd())

        self.first_heating_time_path = self.model_path + 'first_heating_time'
        self.first_heating_energy_path = self.model_path + 'first_heating_energy'
        self.second_heating_time_path = self.model_path + 'second_heating_time'
        self.second_heating_energy_path = self.model_path + 'second_heating_energy'
        self.maintain_path = self.model_path + 'maintain'
        self.press_path = self.model_path + 'press'
        self.cutting_path = self.model_path + 'cutting'
        self.treatment_time_path = self.model_path + 'treatment_time'
        self.treatment_energy_path = self.model_path + 'treatment_energy'

        self.first_heating_time_model = None
        self.first_heating_energy_model = None
        self.reheating_time_model = None
        self.reheating_energy_model = None
        self.maintain_energy_model = None
        self.forging_time_model = None
        self.cutting_time_model = None
        self.heat_treating_time_model = None
        self.heat_treating_energy_model = None
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

        self.door_count = 0

    def heating_time_prediction(self, name, job_list):
        """
        if heating process first operate or middle operate
        :param equipment: heating equipment entity
        :param total_weight:
        :param max_weight:
        :return: completion_time (seconds)
        """
        #형록
        #구현했는데 인자 안맞다고함...
        #reheating, heating 차이가 무엇??
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
        data = furnace_num.TxtToCode(name[-1])
        tmp = [total_weight, max_weight]
        data.extend(tmp)
        heating_time = int(self.first_heating_time_model.predict(data))
        #print('heating time :', heating_time)
        return heating_time

        """if state:
            # if already process is running
            # completion_time = 60  # 재가열 30분
            # completion_time += random.gauss(0, 1)
            # completion_time *= 60
            data = [total_weight, max_weight, len(equipment.job_id_list())]
            # print(data)
            completion_time = self.reheating_time_model.predict(data)
            if completion_time < 60:
                completion_time += 60
            completion_time *= 60

        else:
            # completion_time = 48.281 - (0.085 * total_weight) + (0.655 * max_weight)  # hour
            # completion_time *= 3600  # hour

            data = furnace_num.TxtToCode(equipment.id[-1])
            tmp = [total_weight, max_weight]
            # print(equipment.id, 'total weight ', total_weight, ' /max weight ', max_weight)
            data.extend(tmp)
            completion_time = self.first_heating_time_model.predict(data)
            # completion_time += 10
            # exit(0)
            completion_time *= 3600
        # print('heating_time_prediction takes ', time.time() - s)
        return float(completion_time)"""

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

    def forging_time_prediction(self, job):

        #self.forging_time_model.predict(data)
        """
        weight, current_round, product_name, total_round
        outer - 15분(+N(0.1))CASE_OUTER_PIECE
        piece - 30분(+N(0.1))CASE_SUCTION_PIECE
        shaft - 50분(+N(0.1))SHAFT
        :param equipment: forging equipment entity
        :param forge_type:
        :return: completion_time (seconds)
        """
        forging_time = 1800
        forging_time += random.gauss(0, 1) * 60
        return 60
    """
        size = ['small', 'medium', 'big']

        data = []

        weight = weight #job의 weight
        if weight <= 15 or None:
            product_size = size[0]
        elif weight <= 25:
            product_size = size[1]
        else:
            product_size = size[2]

        tmp = press_product_type.TxtToCode(job['properties']['product']['product_type'])
        data.extend(tmp)
        tmp = press_product_type.TxtToCode(product_size)
        data.extend(tmp)
        data.append(weight)
        data.append(product.properties['total_round'])
        data.append(product.properties['current_round'])
        forging_time = self.forging_time_model.predict(data)

        #return float(forging_time)
    """
    def cutting_time_prediction(self, job):
        weight = job['properties']['ingot']['current_weight']
        tmp = cutter_ingot_type.TxtToCode(job['properties']['ingot']['type'])
        prod_count = len(job['properties']['product_id_list'])

        data = [weight]
        data.extend(tmp)
        data.append(prod_count)

        cutting_time = self.cutting_time_model.predict(data)
        return float(cutting_time)

    def treatment_time_prediction(self, name, job_list):

        total_weight = 0
        max_weight = 0
        ingot_count = 0
        total_count = len(job_list)
        ingot_types = {}
        max_ingot_type = None
        product_count = {}
        treatment_num = name[-1]

        for job in job_list:
            weight = job['properties']['ingot']['current_weight']
            total_weight += weight
            if max_weight < weight:
                max_weight = weight
            product_id = job['properties']['product_id_list'][0]
            product_count[product_id] = 1
            ingot_type = job['properties']['product']['ingot_type_list'][0]
            if ingot_type not in [*ingot_types]:
                ingot_types[ingot_type] = 0
                ingot_count += 1
            ingot_types[ingot_type] += 1

        max_ingot_count = 0
        for key, value in ingot_types.items():
            if max_ingot_count < value:
                max_ingot_count = value
                max_ingot_type = key

        tmp = heat_treatmnet_ingot_type.TxtToCode(max_ingot_type)
        tmp2 = furnace_num.TxtToCode(treatment_num)
        data = [total_weight, max_weight, total_count, ingot_count] + tmp + [len([*product_count])] + tmp2
        treat_time = int((self.heat_treating_time_model.predict(data) + 7) * 60)

        if Debug_mode:
            print('treat time :', treat_time)
        return treat_time
        #---

        """
        :param equipment: treatment equipment entity
        :param parameter:
        :return: completion_time (seconds)
        """
        """
        # 15시간으로 테스트
        # treat cooling time 까지 포함
        # 12 + 6 + 2
        total_weight = 0
        max_weight = 0
        ingot_count = 0
        total_count = len(job_id_list)
        ingot_types = {}
        max_ingot_type = None
        produce_count = {}
        treatment_NO = equipment.id[-1]
        for job_id in job_id_list:
            job = entity_mgr.get(job_id)
            weight = job.get_weight(entity_mgr)
            total_weight += weight
            if max_weight < weight:
                max_weight = weight
            product = entity_mgr.get(job.product_id_list()[0])
            produce_count[product.name()] = 1
            ingot_type = product.properties['ingot_type_list'][0]
            if ingot_type not in [*ingot_types]:
                ingot_types[ingot_type] = 0
                ingot_count += 1
            ingot_types[ingot_type] += 1

        cnt = 0
        for key, value in ingot_types.items():
            if value > cnt:
                cnt = value
                max_ingot_type = key

        tmp = heat_treatmnet_ingot_type.TxtToCode(max_ingot_type)
        tmp2 = furnace_num.TxtToCode(treatment_NO)
        data = [total_weight, max_weight, total_count, ingot_count] + tmp + [len([*produce_count])] + tmp2

        treat_time = self.heat_treating_time_model.predict(data)
        treat_time += 7
        treat_time *= 3600

        return float(treat_time)
        """

    def treatment_cooling_time_prediction(self, equipment, parameter=None):
        """

        :param equipment: treatment equipment entity
        :param parameter:
        :return: completion_time (seconds)
        """
        # 6시간
        treat_time = 64800
        treat_time += random.gauss(0, 1) * 3600
        return treat_time  # random.randint(10, 15)

    def convey_time_prediction(self, job):
        """
        이동시간 현재 3분,,,
        :param current: current equipment
        :param next: next equipment
        :return: complete time (seconds)
        """

        return 180  # random.randint(60, 90)

    def cal_heating_energy_usage(self, equipment, total_weight=None, max_weight=None, time=None):
        """

        :param equipment: heating equipment
        :param time: how long use the equipment (hour !!!!!)
        :return: energy_usage
        """

        if total_weight == 0 and max_weight == 0:
            return 0

        time /= 3600
        if equipment is None:
            return 150  # 최솟값 반환

        state = equipment.state()
        completion_usage = False
        if state:
            # if already process is running
            # re-heating
            # 재 가열시 현재 내부에 있는 모든 ingot과 문 열림 시간으로 계산
            # completion_usage = 150

            data = [time, total_weight, max_weight, len(equipment.job_id_list())]
            completion_usage = self.reheating_energy_model.predict(data)
        else:
            # if it is not running
            if time is None:
                print("need to time")
                exit(1)

            data = furnace_num.TxtToCode(equipment.id[-1])
            tmp = [time, total_weight, max_weight]
            data.extend(tmp)
            completion_usage = self.first_heating_energy_model.predict(data)
        # print(completion_usage)
        # exit(0)
        return completion_usage

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

    def cal_forging_energy_usage(self, equipment, time=None):
        """

        :param equipment: heating equipment
        :param time: how long use the equipment
        :return: energy_usage
        """

        if time is None:
            print('need to forge type')
            exit(0)

        forging_time = (time / 60) * 200
        return 0  # forging_time

    def cal_cutting_energy_usage(self, equipment, time=None):
        """

        :param equipment: heating equipment
        :param time: how long use the equipment
        :return: energy_usage (KW)
        """
        cutting_time = (time / 60) * 200
        return 0  # cutting_time

    def cal_treatment_energy_usage(self, entity_mgr, equipment, job_id_list, time=None):
        """

        :param equipment: heating equipment
        :param time: how long use the equipment
        :return: energy_usage
        """

        if time is None:
            print('time is need')
            exit(1)
        total_weight = 0
        max_weight = 0
        ingot_count = 0
        total_count = len(job_id_list)
        if total_count == 0:
            return 0
        ingot_types = {}
        max_ingot_type = None
        produce_count = {}
        max_ingot_prod = None
        treatment_NO = equipment.id[-1]
        for job_id in job_id_list:
            job = entity_mgr.get(job_id)
            weight = job.get_weight(entity_mgr)
            total_weight += weight
            if max_weight < weight:
                max_weight = weight
            product = entity_mgr.get(job.product_id_list()[0])
            if product.name() not in [*produce_count]:
                produce_count[product.name()] = 0
            produce_count[product.name()] += 1
            ingot_type = product.properties['ingot_type_list'][0]
            if ingot_type not in [*ingot_types]:
                ingot_types[ingot_type] = 0
                ingot_count += 1
            ingot_types[ingot_type] += 1

        usage = 2500 + total_weight

        cnt = 0
        for key, value in ingot_types.items():
            if value > cnt:
                cnt = value
                max_ingot_type = key

        cnt = 0
        for key, value in produce_count.items():
            if value > cnt:
                cnt = value

        tmp = heat_treatmnet_ingot_type.TxtToCode(max_ingot_type)
        tmp2 = furnace_num.TxtToCode(treatment_NO)
        data = [total_weight, max_weight, total_count, ingot_count] + tmp + [len([*produce_count])] + tmp2 + [
            time / 3600]

        usage = self.heat_treating_energy_model.predict(data)

        return usage

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