import util
import numpy

try:
    import vrep
except:
    print ('--------------------------------------------------------------')
    print ('"vrep.py" could not be imported. This means very probably that')
    print ('either "vrep.py" or the remoteApi library could not be found.')
    print ('Make sure both are in the same folder as this file,')
    print ('or appropriately adjust the file "vrep.py"')
    print ('--------------------------------------------------------------')
    print ('')

connectionAddress = '127.0.0.1'
connectionPort = 19997
waitUntilConnected = True
doNotReconnectOnceDisconnected = True
timeOutInMs = 5000
commThreadCycleInMs = 5

vrep.simxFinish(-1)  # just in case, close all opened connections
clientID = vrep.simxStart(connectionAddress, connectionPort, waitUntilConnected, doNotReconnectOnceDisconnected,
                          timeOutInMs, commThreadCycleInMs)

assert clientID != -1, 'Could not connect to VREP to remote API server'

cache = {}


def __cache(function, args, output):
    '''
    Caches the function-argument.
    MUST BE USED ONLY FOR FUNCTIONS WHOSE RESPONSE WILL NOT CHANGE OVER TIME FOR THE ARGS
    :param function:
    :param args:
    :param output:
    :return:
    '''
    global cache
    if not cache.get(function.__name__, False):
        cache[function.__name__] = {}

    cache[function.__name__][args] = output


def __get_cached(function, args):
    try:
        return cache[function.__name__][args]
    except:
        raise ReferenceError


def __check_resp(response, expected):
    '''
    :param response:
    :param expected:
    :return: Throws an exception during unexpected response , else returns true
    '''
    if response == expected:
        return True
    else:
        print ('Remote API function call returned with error code: ', response)
        raise Exception


def get_bodies():
    '''
    TODO: Not working
    Blocking call
    :return: List of kinematic bodies
    '''
    res, h, i, f, s = vrep.simxGetObjectGroupData(clientID, vrep.sim_object_shape_type, 0, vrep.simx_opmode_blocking)

    # res, objs = vrep.simxGetObjects(clientID, vrep.sim_shape_multishape_subtype, vrep.simx_opmode_blocking)
    print i

    __check_resp(res, vrep.simx_return_ok)

    return s


def get_robot(name='IRB4600#'):
    '''
    :param name: name of the robot in the scene
    :return: Robot handle
    '''
    res, robotHandle = vrep.simxGetObjectHandle(clientID, name, vrep.simx_opmode_oneshot_wait)
    __check_resp(res, vrep.simx_return_ok)
    return robotHandle


def get_robot_dof_values(robot_handle):
    #TODO
    pass



def get_joints(robot_handle):
    '''
    This is a very costly function due to recursive blocking calls.
    Need to be optimized

    normally, when using the regular API, you could use function simGetObjectsInTree. That function is not (yet) implemented in the remote API.

    As a workaround, you have several possibilities:

    You could modify the remote API in order to support that function. This is rather difficult and not recommended.
    You could use function simxGetObjectGroupData. You would retrieve all objects and all parent objects. From there you could rebuild the desired tree hierarchy.
    You can use simxGetObjectChild as you mention it, in an iterative way, until you have retrieved all objects in the tree.
    You can retrieve (or continuously stream) the tree objects: on the V-REP side, use simGetObjectsInTree. Then pack the returned table in a string signal.
    Then send that signal to the remote API client, that will decode the string and retrieve the handles. On the V-REP side, inside of a non-threaded child script:

    :param robot_handle:
    :return: robot_joints: map of joint handles to their names
    '''
    try:
        return __get_cached(get_joints, robot_handle)
    except:
        pass


    # 0: Return names
    return_code, handles, intData, floatData, stringData = vrep.simxGetObjectGroupData(clientID,
                                                                                       vrep.sim_object_joint_type, 0,
                                                                                       vrep.simx_opmode_blocking)
    handes_name_map = {}
    for i, h in enumerate(handles):
        handes_name_map[h] = stringData[i]

    queue = []
    queue.append(robot_handle)
    robot_joint_handle_name_map = {}

    while len(queue) > 0:
        parent_handle = queue.pop(0)
        child_handle = 0
        child_index = 0
        while child_handle != -1:
            return_code, child_handle = vrep.simxGetObjectChild(clientID, parent_handle, child_index,
                                                                vrep.simx_opmode_blocking)
            __check_resp(return_code, vrep.simx_return_ok)
            if child_handle != -1:
                child_index = child_index + 1
                queue.append(child_handle)
                if child_handle in handes_name_map:
                    robot_joint_handle_name_map[child_handle] = handes_name_map.get(child_handle)

    __cache(get_joints, robot_handle, robot_joint_handle_name_map)

    return robot_joint_handle_name_map


def create_pose(transform_matrix=numpy.eye(4)):
    '''
    Creates a shape of type 'dummy' in the scene
    :param transform_matrix:
    :return: None
    '''
    size = 0.01
    res, dummy_handle = vrep.simxCreateDummy(clientID, size, None, vrep.simx_opmode_blocking)
    __check_resp(res, vrep.simx_return_ok)

    position = util.get_position_from_matrix(transform_matrix)
    quat = util.get_quat_from_matrix(transform_matrix)

    res = vrep.simxSetObjectQuaternion(clientID, dummy_handle, -1, quat, vrep.simx_opmode_blocking)
    __check_resp(res, vrep.simx_return_ok)

    res = vrep.simxSetObjectPosition(clientID, dummy_handle, -1, position, vrep.simx_opmode_blocking)
    __check_resp(res, vrep.simx_return_ok)


def load_model(path, file_on_server=True):
    '''
    clientID: the client ID. refer to simxStart.
    path: the model filename, including the path and extension ("ttm"). The file is relative to the client or server system depending on the options value (see next argument)
    options: options, bit-coded: bit0 set: the specified file is located on the client side (in that case the function will be blocking since the model first has to be transferred to the server). Otherwise it is located on the server side
    operationMode: a remote API function operation mode. Recommended operation mode for this function is simx_opmode_blocking
    '''
    res, handle = vrep.simxLoadModel(clientID, path, not file_on_server, vrep.simx_opmode_blocking)
    __check_resp(res, vrep.simx_return_ok)
    return res, handle


def load_robot(path, file_on_server=True):
    '''
    :param path:
    :param file_on_server: Is the file on the v-rep server or the client
    :return: response , handle of the loaded robot
    '''
    res, handle = load_model(path=path, file_on_server=file_on_server)
    return res, handle


def get_body_named(name):
    '''
    :param name: name of the body
    :return: Returns the handle of the body
    '''
    pass


def load_env(xml):
    #TODO later
    pass


def get_transform(object_handle):
    '''
    :param object_handle:
    :return: Transform matrix of the object
    '''
    pass


def get_transform_named(object_name):
    '''
    :param object_name:
    :return: The transformation matrix of the object_name
    '''
    return get_transform(get_body_named(object_name))


def get_translation(object_handle):
    '''
    :param object:
    :return: Return the x, y, z translation of the object
    '''
    pass


def get_rotation(object_handle):
    '''
    :param object_handle:
    :return: Return the quaternion w, x, y, z
    '''
    pass


def set_transform(object_handle, transform_matrix):
    '''
    :param object_handle:
    :param transform_matrix: Returns the transform matrix (numpy matrix)
    :return:
    '''
    pass



