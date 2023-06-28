import os
import pickle
import random

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from utils import subspace
from sklearn.svm import SVR


def create_subspaces_and_store(n_clusters=8):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
    # path1 = os.path.join(path, 'sampling/olddata/firstbatch_500Samples.csv')
    # path2 = os.path.join(path, 'sampling/olddata/secondbatch_500Samples.csv')
    # df1 = pd.read_csv(path1, sep=',')
    # df2 = pd.read_csv(path2, sep=',')
    # df = pd.concat([df1, df2])
    df=pd.read_csv(os.path.join(path, 'sampling/newdata/Cleaned_data.csv'), sep=',')
    cols = df.drop(columns=['Speed'], axis=1).columns
    # creating subspaces based on the sample data 
    # print(cols)
    clusters_return = subspace.subspace_by_clustering(k=n_clusters, data=df[cols])
    # get currenty directory
    with open(path + "/utils/pickles/cluster_bounds", "wb") as pickewriter:  # Pickling cluster bounds for pso
        pickle.dump(clusters_return['cluster_bounds'], pickewriter)
    with open(path + "/utils/pickles/kmeans_classifier",
              "wb") as pick:  # Pickling classifier for further use on new locations
        pickle.dump(clusters_return['kmeans'], pick)


def create_objectivefunction_for_subspaces():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
    df=pd.read_csv(os.path.join(path, 'sampling/newdata/Cleaned_data.csv'), sep=',')
    cols = df.drop(columns=['Speed'], axis=1).columns

    # path1 = os.path.join(path, 'sampling/olddata/firstbatch_500Samples.csv')
    # path2 = os.path.join(path, 'sampling/olddata/secondbatch_500Samples.csv')
    # df1 = pd.read_csv(path1, sep=',')
    # df2 = pd.read_csv(path2, sep=',')
    # df = pd.concat([df1, df2])
    # df.drop(columns=['Unnamed: 0'], inplace=True)
    # cols = df.drop(columns=['Speed'], axis=1).columns
    with open(path + "/utils/pickles/kmeans_classifier", "rb") as f:
        model = pickle.load(f)
    clusters = []
    for index, row in df[cols].iterrows():
        temp = row.values
        temp = np.array(temp).reshape(1, 6)
        clusters.append(model.predict(temp)[0])
    df['Cluster'] = clusters
    models = []
    feautre_imp=[]
    mses=[]
    for i in range(model.n_clusters):
        sub_df = df[df['Cluster'] == i]
        X = sub_df.drop(columns=['Speed', 'Cluster'], axis=1).values
        y = sub_df.Speed.values

        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)

        regr = RandomForestRegressor(random_state=42, criterion='squared_error')
        regr.fit(X_train, y_train)
        y_pred = regr.predict(X_test)

        #feature importance
        # print('feature importance',regr.feature_importances_)
        feautre_imp.append(regr.feature_importances_)
        # print('R^2 score: ', regr.score(X_test, y_test))
        # print('MSE : ', mean_squared_error(y_test, y_pred))
        mses.append(mean_squared_error(y_test, y_pred))
        models.append(model)
        ###############################
        # SVR
  

        # svr = SVR(C=1.0, epsilon=0.2)
        # svr.fit(X_train, y_train)

        # y_pred = svr.predict(X_test)

        # # print('R^2 score: ',svr.score(X_test, y_test))
        # print('MSE : ', mean_squared_error(y_test, y_pred))
        # mses.append(mean_squared_error(y_test, y_pred))
        # models.append(svr)

        ###############################
        # model = LinearRegression()

        # # Train it
        # model.fit(X_train, y_train)

        # # Make prediction
        # y_pred = model.predict(X_test)
        # #  Evaluate the model
        # # print('R^2 score: ', model.score(X_test, y_test))
        # # print('MSE : ', mean_squared_error(y_test, y_pred))
        # mses.append(mean_squared_error(y_test, y_pred))
        # models.append(model)


        ######
        # model=DecisionTreeRegressor()
        # model.fit(X_train, y_train)
        # y_pred = model.predict(X_test)
        # #  Evaluate the model
        # # print('R^2 score: ', model.score(X_test, y_test))
        # print('MSE : ', mean_squared_error(y_test, y_pred))
        # mses.append(mean_squared_error(y_test, y_pred))
        # models.append(model)
    print('feature importance',np.mean(feautre_imp,axis=0))
    print('MSE : ', np.mean(mses))
    with open(path + "/utils/pickles/subspace_models", "wb") as pick:
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
        if bounds[i][0] <= temp[i] <= bounds[i][1]:
            counter += 1

    return counter == 6


def pso(space, regr):
    # Define the problem-specific parameters
    num_particles = 30
    max_iterations = 300
    # [[0, 10], [0, 90], [-90, 90], [-90, 90], [-90, 90], [0, 90]] Define the search space for each parameter
    search_space = space
    inertia = 0.5
    cognitive_constant = 0.8
    social_constant = 2.2
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
            velocity = (inertia * np.array(velocity) + cognitive_constant * random.uniform(0, 1) * (
                        np.array(personal_best_position) - np.array(position)) + social_constant * random.uniform(0,1) * (np.array(personal_best_position) - np.array(position)))

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


def get_subspace_optimas():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
    with open(path + "/utils/pickles/cluster_bounds", "rb") as f:
        cluster_bounds = pickle.load(f)

    with open(path + "/utils/pickles/subspace_models", "rb") as f:
        subspace_models = pickle.load(f)
    subspace = np.array(cluster_bounds)
    bounds = []
    optimums = []
    for i in range(len(cluster_bounds)):
        space = np.array(cluster_bounds[i])
        optimums.append(pso(space, subspace_models[i]))
    DF = pd.DataFrame(optimums, index=range(len(optimums)),
                      columns=['Snelheid', 'Omvang1', 'Positie1', 'Omvang2', 'Positie2', 'Relatie'])
    DF.to_csv(path + "/utils/pickles/optimums.csv")

def merging_datasets():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
    data1=pd.read_csv(path+'/sampling/newdata/NewParameterSamples_0-200.csv')
    speed1=pd.read_csv(path+'/sampling/newdata/speed_data_new_0-200.csv')
    speed1=speed1[speed1['Time']>='11:46:00.000']
    speed1.columns=['Timestamp','Speed']
    t=pd.merge(speed1,data1,on=['Timestamp'],how='outer')
    t=t.sort_values(by='Timestamp')
    for i in t.columns:
        if i!='Timestamp' and i!='Speed':
            t[i]=t[i].fillna(method='ffill')
    t=t.dropna(subset=['Snelheid'])        
    t['Speed']=t['Speed'].fillna(method='bfill')
    results=t.groupby(['Snelheid', 'Omvang1', 'Positie1', 'Omvang2','Positie2', 'Relatie']).agg({'Speed':np.mean})
    Final1=results.reset_index()
    ####
    data2=pd.read_csv(path+'/sampling/newdata/NewParameterSamples_201-500.csv')
    speed2=pd.read_csv(path+'/sampling/newdata/speed_data_new_201-500.csv')
    speed2=speed2[speed2['Time']>='09:22:00.000']
    speed2.columns=['Timestamp','Speed']
    t=pd.merge(speed2,data2,on=['Timestamp'],how='outer')
    t=t.sort_values(by='Timestamp')
    for i in t.columns:
        if i!='Timestamp' and i!='Speed':
            t[i]=t[i].fillna(method='ffill')
    t=t.dropna(subset=['Snelheid'])        
    t['Speed']=t['Speed'].fillna(method='bfill')
    results=t.groupby(['Snelheid', 'Omvang1', 'Positie1', 'Omvang2','Positie2', 'Relatie']).agg({'Speed':np.mean})
    Final2=results.reset_index()
    ###
    Final=pd.concat([Final1,Final2])
    ####
    outliers=pd.read_csv(path+'/sampling/newdata/outliers.csv')
    ####
    for index,row in outliers.iterrows():
        Final=Final[~((Final['Snelheid']==row['Snelheid'])&(Final['Omvang1']==row['Omvang1'])&(Final['Positie1']==row['Positie1'])&(Final['Omvang2']==row['Omvang2'])&(Final['Positie2']==row['Positie2'])&(Final['Relatie']==row['Relatie']))]
    Final.to_csv(path+'/sampling/newdata/Cleaned_data.csv',index=False)