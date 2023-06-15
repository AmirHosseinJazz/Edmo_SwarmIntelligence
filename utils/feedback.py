import numpy as np 

def Nearest_Optima(optimas, location):
    """
    Find the nearest optima to the current location
    optimas: (n, 6) array of optimas
    location: (6,) array of current location
    """
    dist = np.linalg.norm(optimas - location, axis=1)
    return np.argmin(dist)

def movement_toward_nearest_optima(optimas,locations):
    """
    Find the direction of the movement toward the nearest optima
    optimas: (n, 6) array of optimas
    locations: (4, 6) array of locations
    """
    nearest_optima = Nearest_Optima(optimas, locations[-1])
    distance_to_nearest_optima = np.linalg.norm(optimas[nearest_optima] - locations[-1])
    distance_to_nearest_optima_previous_1 = np.linalg.norm(optimas[nearest_optima] - locations[-2])
    distance_to_nearest_optima_previous_2 = np.linalg.norm(optimas[nearest_optima] - locations[-3])
    distance_to_nearest_optima_previous_3 = np.linalg.norm(optimas[nearest_optima] - locations[-4])

    movement=np.array([distance_to_nearest_optima,distance_to_nearest_optima_previous_1,distance_to_nearest_optima_previous_2,distance_to_nearest_optima_previous_3])
    

    # check if movement is monotonically increasing
    if np.all(np.diff(movement) > 0):
        print('Time for feedback')
        provide_feedback(nearest_optima,locations[-1])
    else:
        pass

def provide_feedback(optima,location):
    """
    Provide feedback to the user
    optima: (6) array of optimas
    location: (6,) array of current location
    """
    # finding the biggest difference between the elements of the two arrays
    diff = np.abs(optima - location)
    max_diff = np.max(diff)
    # finding the index of the biggest difference
    index = np.argmax(diff)
    # finding the sign of the difference
    sign = np.sign(optima[index] - location[index])
    # print the feedback
    if index == 0:
        print('Move the Snelheid by {} degrees'.format(max_diff*sign))
    elif index == 1:
        print('Move the Omvang1 by {} degrees'.format(max_diff*sign))
    elif index == 2:
        print('Move the Positie1 by {} degrees'.format(max_diff*sign))
    elif index == 3:
        print('Move the Omvang2 by {} degrees'.format(max_diff*sign))
    elif index == 4:
        print('Move the Positie2 by {} degrees'.format(max_diff*sign))
    elif index == 5:
        print('Move the Relatie by {} degrees'.format(max_diff*sign))
    