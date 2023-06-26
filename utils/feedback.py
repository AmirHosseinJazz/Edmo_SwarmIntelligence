import numpy as np


def Nearest_Optima(optimas, location):
    """
    Find the nearest optima to the current location
    optimas: (n, 6) array of optimas
    location: (6,) array of current location
    """
    distances = []
    for d in optimas:
        distances.append(np.linalg.norm(d - location))
    return np.argmin(distances)


def movement_toward_nearest_optima(optimas, locations):
    """
    Find the direction of the movement toward the nearest optima
    optimas: (n, 6) array of optimas
    locations: (4, 6) array of locations
    """
    nearest_optima = Nearest_Optima(optimas, locations[-1])
    distance_to_nearest_optima = np.linalg.norm(optimas[nearest_optima] - locations[-1])
    distance_to_nearest_optima_previous_1 = np.linalg.norm(optimas[nearest_optima] - locations[-2])
    distance_to_nearest_optima_previous_2 = np.linalg.norm(optimas[nearest_optima] - locations[-3])

    movement = np.array(
        [distance_to_nearest_optima, distance_to_nearest_optima_previous_1, distance_to_nearest_optima_previous_2])

    # print(movement)
    # check if movement is monotonically increasing
    if np.all(np.diff(movement) > 0):
        print('Time for feedback')
        return provide_feedback(optimas[nearest_optima], locations[-1])
    else:
        print('No feedback')
        return [0, 0, 0, 0, 0, 0]


def provide_feedback(optima, location):
    """
    Provide feedback to the user
    optima: (6) array of optimas
    location: (6,) array of current location
    """
    # finding the biggest difference between the elements of the two arrays
    # print(optima)
    # print(location)
    diff = np.abs(optima - location)
    # print(diff)
    max_diff = np.max(diff)
    # finding the index of the biggest difference
    index = np.argmax(diff)
    # finding the sign of the difference
    sign = np.sign(optima[index] - location[index])
    # print the feedback
    if index == 0:
        print('Move the Snelheid by {} degrees'.format(max_diff * sign))
        return [1 * sign, 0, 0, 0, 0, 0]
    elif index == 1:
        print('Move the Omvang1 by {} degrees'.format(max_diff * sign))
        return [0, 1 * sign, 0, 0, 0, 0]
    elif index == 2:
        print('Move the Positie1 by {} degrees'.format(max_diff * sign))
        return [0, 0, 1 * sign, 0, 0, 0]
    elif index == 3:
        print('Move the Omvang2 by {} degrees'.format(max_diff * sign))
        return [0, 0, 0, 1 * sign, 0, 0]
    elif index == 4:
        print('Move the Positie2 by {} degrees'.format(max_diff * sign))
        return [0, 0, 0, 0, 1 * sign, 0]
    elif index == 5:
        print('Move the Relatie by {} degrees'.format(max_diff * sign))
        return [0, 0, 0, 0, 0, 1 * sign]
