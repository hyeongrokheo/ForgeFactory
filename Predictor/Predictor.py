from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from Predictor.DnnRegression import *
from Predictor.OneHotVectorCode import *
from UtilFunction import *

import random
import os

class Predictor:
    def __init__(self, type):
        self.type = type
        if self.type == 'Planning':
            self.model_path = '/ForgeFactory/Predictor/Models/'
        elif self.type == 'Real':
            self.model_path = '/ForgeFactory/Predictor/Models_VF/'
        else:
            print('Error : predictor type error')
            exit(1)
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
                return 0

            tmp = [total_weight, max_weight]
            data = furnace_num.TxtToCode(name[-1])
            data.extend(tmp)
            heating_time = int(self.first_heating_time_model.predict(data)) * 60
            return heating_time
        elif self.type == 'Real':
            return 300

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
        weight = job['properties']['ingot']['current_weight']
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
        data.append(total_round)
        data.append(current_round)

        forging_time = int(self.forging_time_model.predict(data) / 60)
        #print('forging_time :', forging_time)
        return forging_time

    # 구현완료
    def cutting_time_prediction(self, job):
        weight = job['properties']['ingot']['current_weight']
        tmp = cutter_ingot_type.TxtToCode(job['properties']['ingot']['type'])
        prod_count = len(job['properties']['product_id_list'])

        data = [weight]
        data.extend(tmp)
        data.append(prod_count)

        cutting_time = int(self.cutting_time_model.predict(data) / 60)
        #print('cutting time :', cutting_time)
        return cutting_time

    # 구현완료
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
            None
            #print('treat time :', treat_time)
        return treat_time

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
        for j in job_list:
            weight = j['properties']['ingot']['current_weight']
            total_weight += weight
            if max_weight < weight:
                max_weight = weight
        data = furnace_num.TxtToCode(name[-1])
        tmp = [heating_time, total_weight, max_weight]
        data.extend(tmp)
        heating_energy = self.first_heating_energy_model.predict(data)

        #print('heating energy :', energy_usage)
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

    def treatment_energy_prediction(self, name, job_list, treatment_time):
        total_weight = 0
        max_weight = 0
        ingot_count = 0
        total_count = len(job_list)
        if total_count == 0:
            return 0
        ingot_types = {}
        max_ingot_type = None
        product_count = {}
        treatment_NO = name[-1]
        for job in job_list:
            weight = job['properties']['ingot']['current_weight']
            total_weight += weight
            if max_weight < weight:
                max_weight = weight
            #product = entity_mgr.get(job.product_id_list()[0])
            for product_id in job['properties']['product_id_list']:
                if product_id not in [*product_count]:
                    product_count[product_id] = 0
                product_count[product_id] += 1
            ingot_type = job['properties']['product']['ingot_type_list'][0]
            if ingot_type not in [*ingot_types]:
                ingot_types[ingot_type] = 0
                ingot_count += 1
            ingot_types[ingot_type] += 1

        cnt = 0
        for key, value in ingot_types.items():
            if cnt < value:
                cnt = value
                max_ingot_type = key

        cnt = 0
        for key, value in product_count.items():
            if cnt < value:
                cnt = value

        tmp = heat_treatmnet_ingot_type.TxtToCode(max_ingot_type)
        tmp2 = furnace_num.TxtToCode(treatment_NO)
        data = [total_weight, max_weight, total_count, ingot_count] + tmp + [len([*product_count])] + tmp2 + [treatment_time / 3600]

        treatment_energy = self.heat_treating_energy_model.predict(data)

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
