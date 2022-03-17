from UtilFunction import *

class TreatmentFurnace:
    def __init__(self, env, allocator):
        self.env = env
        self.alloc = allocator

        self.name = 'treatment_furnace'

        self.treatment_job_list = []

        if Debug_mode:
            print(self.name + ' :: created')

    def run(self):
        while True:
            # print('time :', self.env.now)
            yield self.env.timeout(5)
            new_job = self.alloc.get_next_treatment_job()
            if new_job:
                # print('job :', new_job)
                self.treatment_job_list.append(new_job)
