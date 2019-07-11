

class OneHotVector:
    def __init__(self):
        self.text_list = {}

    def getTxtList(self, text_list):
        for i in range(len(text_list)):
            self.text_list[text_list[i]] = i

    def TxtToCode(self, txt):
        arr = [0 for x in range(len(self.text_list))]
        if isinstance(txt, list):
            txt = txt[0]
        try:
            idx = self.text_list[txt]
        except:
            idx = 0
        arr[idx] = 1
        return arr


cutter_ingot_type_list = [u'SC계열', u'합금강', u'탄소강']
cutter_ingot_type_list.sort()
cutter_ingot_type = OneHotVector()
cutter_ingot_type.getTxtList(cutter_ingot_type_list)

furnace_num_list = ['0', '1', '2', '3', '4']
furnace_num_list.sort()
furnace_num = OneHotVector()
furnace_num.getTxtList(furnace_num_list)

heat_treatmnet_ingot_type_list = [u'탄소강', u'합금강']
heat_treatmnet_ingot_type_list.sort()
heat_treatmnet_ingot_type = OneHotVector()
heat_treatmnet_ingot_type.getTxtList(heat_treatmnet_ingot_type_list)

press_product_type_list = ['Plate', 'Cylinder', 'Ring']
press_product_type_list.sort()
press_product_type = OneHotVector()
press_product_type.getTxtList(press_product_type_list)

press_product_size_list = ['small', 'medium', 'large']
press_product_size_list.sort()
press_product_size = OneHotVector()
press_product_size.getTxtList(press_product_size_list)
