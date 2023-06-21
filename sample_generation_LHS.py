import numpy as np
from pyDOE import lhs
import csv

if __name__ == '__main__':
    var1=[x/10 for x in list(range(50,101,10))]
    var2=[x for x in range(30,76,15)]
    var3=[x for x in range(-75,76,15)]
    var4=[x for x in range(30,76,15)]
    var5=[x for x in range(-75,76,15)]
    var6=[-90,-75,-60,-45,-30,30,45,60,75,90]


    # Define the number of dimensions and values per dimension
    num_dimensions = 6
    values_per_dimension = [len(var1), len(var2), len(var3), len(var4), len(var5), len(var6)]

    # Generate the Latin Hypercube Sample
    lhs_sample = lhs(num_dimensions, samples=100, criterion='maximin')

    # Initialize the sampled indices list
    sampled_indices = []

    # Select indices based on the LHS sample
    for dim in range(num_dimensions):
        dim_indices = np.linspace(0, values_per_dimension[dim] - 1, values_per_dimension[dim])
        selected_indices = np.interp(lhs_sample[:, dim], np.linspace(0, 1, values_per_dimension[dim]), dim_indices)
        sampled_indices.append(selected_indices.astype(int))

    # Transpose the sampled indices list
    sampled_indices = np.transpose(sampled_indices)

    # Print the sampled indices
    # for indices in sampled_indices:
        # print(indices)

    all_samples = []
    for indices in sampled_indices:
        all_samples.append([var1[indices[0]], var2[indices[1]], var3[indices[2]], var4[indices[3]], var5[indices[4]], var6[indices[5]]])

    filename = 'samples.csv'

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(all_samples)