import openravepy


def get_position_from_matrix(transform):
    return tuple(openravepy.poseFromMatrix(transform)[4:])


def get_quat_from_matrix(transform):
    """
    OpenRAVE Convention: Quaternions are defined with the scalar value as the first component. For example [w x y z]
    """
    quat = openravepy.poseFromMatrix(transform)[0:4]
    quat.tolist().reverse()
    return tuple(quat)
