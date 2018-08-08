import sys
#Change the below location to suit your vrep installation
sys.path.insert(0, '/home/local/ASUAD/mpookkot/Documents/V-REP_PRO_EDU_V3_5_0_Linux/programming/remoteApiBindings/python/python')

import api
if __name__ == "__main__":
    res, handle = api.load_robot(
        # Robot models are available in the RobotModels repository of AAIR
        path='/home/local/ASUAD/mpookkot/Documents/V-REP_PRO_EDU_V3_5_0_Linux/models/robots/mobile/Fetch.ttm')
    joints = api.get_joints(handle)
    print joints