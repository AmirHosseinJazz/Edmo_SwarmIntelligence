import os

from utils import feedback
from utils import integration
import pandas as pd
import numpy as np
# hide warnings
import warnings

warnings.filterwarnings('ignore')


def optimization():
    # merging datasets
    integration.merging_datasets()


    # create subspaces based on our samples and store the classifier and bounds
    integration.create_subspaces_and_store(n_clusters=4)

    # create objective function for each subspace
    integration.create_objectivefunction_for_subspaces()

    # getting the optimums for each subspace using pso , based on the respective objective function
    optimums = integration.get_subspace_optimas()


def retrieve_optimas():
    # retrieve the optimums for each subspace
    df = pd.read_csv('utils/pickles/optimums.csv')
    df = df.drop(columns=['Unnamed: 0'])
    return df


def suggestion(locations=None):
    if locations is None:
        # the rightmost is the latest location (the current location)
        locations = np.array(
            [[-5, -5, -5, -5, -5, -5], [-2, -2, -2, -2, -2, -2], [-1, -1, -1, -1, -1, -1], [0, 0, 0, 0, 90, 0]])
    df = retrieve_optimas()
    optimas = np.array(df.values)
    return_to_gui = feedback.movement_toward_nearest_optima(optimas, locations)
    print(return_to_gui)
    return return_to_gui


if __name__ == "__main__":
    optimization()
    print(retrieve_optimas())
    # suggestion()
