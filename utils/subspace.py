import numpy as np
import pandas as pd
import os
from sklearn.cluster import KMeans

#### Method 1 : Clustering
# get bounds for each dimension of a subspace
def get_subspace_bounds(subspace):
    subspace = np.array(subspace)
    bounds = []
    for dim in range(subspace.shape[1]):
        min_val = np.min(subspace[:, dim])
        max_val = np.max(subspace[:, dim])
        bounds.append((min_val, max_val))
    return bounds

def subspace_by_clustering(k=10):
    # read csv from parent folder
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
    path = os.path.join(path, 'samples.csv')
    data=pd.read_csv(path, sep=',',header=None)
    print(data.head())

    # perform K means clustering
    kmeans = KMeans(n_clusters=k, random_state=0).fit(data)
    # get number of clusters
    n_clusters = len(np.unique(kmeans.labels_))
    print('number of clusters: ', n_clusters)
    cluster_bounds =[]
    # get bounds for each cluster
    for i in range(n_clusters):
        dt=data[kmeans.labels_==i]
        print('cluster ', i, ' size: ', len(dt))
        bounds=get_subspace_bounds(dt)
        print('cluster ', i, ' bounds: ', bounds)
        cluster_bounds.append(bounds)
    return {'cluster_bounds': cluster_bounds, 'kmeans': kmeans}



##### Method 2
def subspace_by_values(k=10):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
    path = os.path.join(path, 'samples.csv')
    data=pd.read_csv(path, sep=',',header=None)
    # print(data.head())

    # convert to numpy array
    data = data.values
    # print(data)

    subspaces = recursive_binary_partitioning(data)
    subspace_bounds=[]
    for subspace in subspaces:
        subspace_bounds.append(get_subspace_bounds(subspace))
    return {'subspace_bounds': subspace_bounds}

def recursive_binary_partitioning(data, num_subspaces=8, dimension=0):
    if num_subspaces <= 1:
        return [data]
    
    # Sort the data along the selected dimension
    sorted_data = sorted(data, key=lambda x: x[dimension])
    
    # Find the split point
    split_index = len(sorted_data) // 2
    split_point = sorted_data[split_index][dimension]
    
    # Create two subspaces
    subspace1 = sorted_data[:split_index]
    subspace2 = sorted_data[split_index:]
    
    # Recurse on each subspace
    subspaces1 = recursive_binary_partitioning(subspace1, num_subspaces // 2, (dimension + 1) % 6)
    subspaces2 = recursive_binary_partitioning(subspace2, num_subspaces // 2, (dimension + 1) % 6)
    
    return subspaces1 + subspaces2

# subspace_by_clustering()
# subspace_by_values()