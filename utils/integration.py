import numpy as np
import pandas as pd
import os
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
import numpy.random as rnd
import time
import matplotlib.pyplot as plt

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import random
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import cross_val_score
import pickle 
from subspace import *

def create_subspaces_and_storing():
    path = os.path.join( '../olddata/firstbatch_500Samples.csv')
    path2 = os.path.join( '../olddata/secondbatch_500Samples.csv')
    df1=pd.read_csv(path, sep=',')
    df2=pd.read_csv(path2, sep=',')
    df=pd.concat([df1,df2])
    # columns = ['Snelheid', 'Omvang1', 'Positie1', 'Relatie', 'Omvang2', "Positie2", 'Speed']
    # df = df[columns]
    cols = df.drop(columns = ['Speed','Unnamed: 0'], axis = 1).columns
    clusters_return=subspace_by_clustering(k=10,data=df[cols])
    with open("models/cluster_bounds", "wb") as pickewriter:   #Pickling
        pickle.dump(clusters_return['cluster_bounds'], pickewriter)
    with open("models/kmeans_classifier", "wb") as pick:   #Pickling
        pickle.dump(clusters_return['kmeans'], pick)

def create_objectivefunction_for_subspaces():
    path = os.path.join( '../olddata/firstbatch_500Samples.csv')
    path2 = os.path.join( '../olddata/secondbatch_500Samples.csv')
    df1=pd.read_csv(path, sep=',')
    df2=pd.read_csv(path2, sep=',')
    df=pd.concat([df1,df2])
    df.drop(columns=['Unnamed: 0'],inplace=True)
    cols = df.drop(columns = ['Speed'], axis = 1).columns
    with open("models/kmeans_classifier", "rb") as f:
        model = pickle.load(f)
    clusters=[]
    for index,row in df[cols].iterrows():
        temp = row.values
        temp = np.array(temp).reshape(1,6)
        clusters.append(model.predict(temp)[0])
    df['Cluster']=clusters       
    models=[]
    for i in range(model.n_clusters):

        sub_df = df[df['Cluster'] == i]
        X = sub_df.drop(columns = ['Speed','Cluster'], axis = 1).values
        y = sub_df.Speed.values

        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.33, random_state = 18)

        regr = RandomForestRegressor(max_depth=6, random_state=42, criterion='squared_error')
        regr.fit(X_train, y_train)
        y_pred = regr.predict(X_test)

        print('R^2 score: ',regr.score(X_test, y_test))
        print('MSE : ', mean_squared_error(y_test, y_pred))

        models.append(regr)

    with open("models/subspace_models", "wb") as pick: 
        pickle.dump(models, pick) 


def fitness_function(model, parameters):

  # intercept = model.intercept_
  # coefs = model.coef_

  # sum = 0  
  # for i in range(6):
  #   sum += (coefs[i] * parameters[i])
  # f = intercept + sum
  return model.predict(np.array(parameters).reshape(1, 6))

def check_constraints(temp, bounds):

  counter = 0

  for i in range(6):
    if temp[i] >= bounds[i][0] and temp[i] <= bounds[i][1] :
      counter += 1

  return counter == 6

def pso(space,regr):

    # Define the problem-specific parameters
    num_particles = 30
    max_iterations = 300
    search_space = space #[[0, 10], [0, 90], [-90, 90], [-90, 90], [-90, 90], [0, 90]] # Define the search space for each parameter
    inertia = 0.5
    cognitive_constant = 1.5
    social_constant = 1.5
    # Initialize the swarm
    swarm = []
    best_positions = []
    global_best_position = None
    global_best_fitness = float('inf')

    for _ in range(num_particles):
        # Initialize particle position and velocity randomly within the search space
        position = [random.uniform(low, high) for low, high in search_space]
        velocity = [random.uniform(-1, 1) for _ in range(6)]
        
        # Evaluate fitness
        fitness = fitness_function(regr, position)
        
        # Initialize personal best position and fitness
        personal_best_position = position
        personal_best_fitness = fitness
        
        # Update global best position and fitness
        if fitness < global_best_fitness:
            global_best_position = position
            global_best_fitness = fitness
        
        # Add particle to the swarm
        swarm.append((position, velocity, personal_best_position, personal_best_fitness))
        best_positions.append(personal_best_position)

    # PSO main loop
    iteration = 0
    while iteration < max_iterations:
        for i in range(num_particles):
            # Update particle velocity and position if constraints are met
            position, velocity, personal_best_position, _ = swarm[i]
            
            # Update velocity
            velocity = (inertia * np.array(velocity) + cognitive_constant * random.uniform(0, 1) * (np.array(personal_best_position) - np.array(position)) + social_constant * random.uniform(0, 1) * (np.array(personal_best_position) - np.array(position)))
            
            # Update position
            position_temp = np.array(position) + np.array(velocity)
            
            if check_constraints(position_temp, search_space):
                position = position_temp

            # Evaluate fitness
            fitness = fitness_function(regr, position)
            
            # Update personal best position and fitness
            if fitness < swarm[i][3]:
                swarm[i] = (position, velocity, position, fitness)
                best_positions[i] = position
            
            # Update global best position and fitness
            if fitness > global_best_fitness:
                global_best_position = position
                global_best_fitness = fitness
        
        iteration += 1

    # Retrieve the optimized solution
    optimized_solution = global_best_position

    # Print or process the optimized solution
    print("Optimized solution:", optimized_solution)

    return optimized_solution


def get_subspace_bounds():
    with open("models/cluster_bounds", "rb") as f:
        cluster_bounds = pickle.load(f)
    
    with open("models/subspace_models", "rb") as f:
        subspace_models = pickle.load(f)
    subspace = np.array(cluster_bounds)
    bounds = []
    optimums = []
    for i in range(len(cluster_bounds)):
        space=np.array(cluster_bounds[i])
        optimums.append(pso(space,subspace_models[i]))
    return optimums

get_subspace_bounds()