
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

path = "C:\grid_96well.json"
try:
    with open(path, 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    print("Error: The file 'data.json' was not found.")
    
x = [] 
y = []   
for well, fov in data.items():
    for id, coord in fov.items():
        x.append(coord["xy"][0])
        y.append(coord["xy"][1])
    
all_index = list(np.arange(68))  
indexes = [5, 6, 7, 9, 10, 11, 20, 21, 22, 27, 28, 29, 38, 39, 40, 46, 47, 48, 35, 36, 37, 49, 50, 51, 52, 53, 54]
# 3*3 fov indexes if we want three of them
fov_1 = [5, 6, 7, 9, 10, 11, 20, 21, 22] # upper left
center_fov_1_ind = 10
fov_1_ctr = data["A1"][str(center_fov_1_ind)]["xy"]
fov_2 = [27, 28, 29, 38, 39, 40, 46, 47, 48] # (quite) in the middle 
center_fov_2_ind = 39
fov_2_ctr = data["A1"][str(center_fov_2_ind)]["xy"]
fov_3 = [35, 36, 37, 49, 50, 51, 52, 53, 54] # lower right
center_fov_3_ind = 50
fov_3_ctr = data["A1"][str(center_fov_3_ind)]["xy"]

# 5*5 fov
fov_5_5 = [8, 9, 10, 11, 12, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 44, 45, 46, 47, 48]
center_5_5 = 27
fov_5_5_center = [x[center_5_5], y[center_5_5]]
fov_5_5_ctr = data["A1"][str(center_5_5)]["xy"]

# Eliminate the coodinates of 3*3 fovs from all indexes
for index in sorted(indexes, reverse=True):
    del all_index[index]

all_index_5_5 = list(np.arange(68)) 
indexes_5_5 = fov_5_5 + fov_3
# Eliminate the coodinates of 5*5 and one 3*3 fov from all indexes
for index in sorted(indexes_5_5, reverse=True):
    del all_index_5_5[index]


# The coordinates of the rest of the points if we use 3 pieces of 3*3 fovs
data1 = pd.DataFrame({
    'x': [x[ind] for ind in indexes],
    'y': [y[ind] for ind in indexes],
    'label': 'Dataset 1'
})

# The coordinates of 3 pieces of 3*3 fovs
data2 = pd.DataFrame({
    'x': [x[ind] for ind in all_index],
    'y': [y[ind] for ind in all_index],
    'label': 'Dataset 2'
})
# To plot them together
combined_data = pd.concat([data1, data1])

# All of the coordinates 
all = pd.DataFrame({
    'x': x,
    'y': y,
    'label': 'Dataset 2'
})

# Enumerate the fovs
labels = []
for i in range(len(x)):
    labels.append(str(i))

# Creating the scatter plot for all the points of one field of view
fig = plt.figure()
ax = fig.add_subplot(111)
sns.scatterplot(data=all, x='x', y='y')
# Adding labels and title
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.title('Scatter Plot of one Field of View')
plt.legend(title='Dataset')

# To label the data points
for i, txt in enumerate(labels):
    ax.text(x[i],y[i], txt)
    
# Display the plot
plt.show()

# Plot the 3*3 fovs with different colors
fig, ax = plt.subplots()
ax.scatter([x[ind] for ind in all_index], [y[ind] for ind in all_index], marker="s", label='rest')
ax.scatter([x[ind] for ind in fov_1],[y[ind] for ind in fov_1], c='g', marker="^", label='fov_1')
ax.scatter([x[ind] for ind in fov_2], [y[ind] for ind in fov_2], c='r', marker="x", label='fov_2')
ax.scatter([x[ind] for ind in fov_3], [y[ind] for ind in fov_3], c='m', marker="o", label='fov_3')
ax.set_ylim([-36000, -28000])
ax.set_xlabel("X-axis")
ax.set_xlabel("Y-axis")
ax.set_title('Only 3x3 Field of Views')
#ax.set_ylim([0, 5])
ax.legend()
plt.show()

# Plot the 5*5 and one 3*3 fov
fig, ax = plt.subplots()
ax.scatter([x[ind] for ind in all_index_5_5], [y[ind] for ind in all_index_5_5], marker="s", label='rest')
ax.scatter([x[ind] for ind in fov_3],[y[ind] for ind in fov_3], c='g', marker="^", label='fov_3')
ax.scatter([x[ind] for ind in fov_5_5], [y[ind] for ind in fov_5_5], c='r', marker="x", label='fov_5_5')
ax.set_ylim([-36000, -28000])
ax.set_xlabel("X-axis")
ax.set_xlabel("Y-axis")
ax.set_title('5x5 and 3x3 Field of Views')
#ax.set_ylim([0, 5])
ax.legend()
plt.show()


# TODO: Move the stage to place then inject then take a photo




"""
    
path = "C:\grid_96well.json"

def fov_stimulate(self, path: str, well: str, fov: str):
    try:
        with open(path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("Error: The file 'data.json' was not found.")
        
    x = [] 
    y = []   
    for wells, fov in data.items():
        for id, coord in fov.items():
            x.append(coord["xy"][0])
            y.append(coord["xy"][1])
    
    all_index = list(np.arange(68))  
    # 3*3 fov indexes if we want three of them
    indexes = [5, 6, 7, 9, 10, 11, 20, 21, 22, 27, 28, 29, 38, 39, 40, 46, 47, 48, 35, 36, 37, 49, 50, 51, 52, 53, 54]
    fov_1 = [5, 6, 7, 9, 10, 11, 20, 21, 22] # upper left
    center_fov_1_ind = 10
    fov_1_ctr = data[well][str(center_fov_1_ind)]["xy"]
    fov_2 = [27, 28, 29, 38, 39, 40, 46, 47, 48] # (quite) in the middle 
    center_fov_2_ind = 39
    fov_2_ctr = data[well][str(center_fov_2_ind)]["xy"]
    fov_3 = [35, 36, 37, 49, 50, 51, 52, 53, 54] # lower right
    center_fov_3_ind = 50
    fov_3_ctr = data[well][str(center_fov_3_ind)]["xy"]
    
    if fov == "5x5":
        # 5*5 fov
        fov_5_5 = [8, 9, 10, 11, 12, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 44, 45, 46, 47, 48]
        center_5_5 = 27
        fov_5_5_center = [x[center_5_5], y[center_5_5]]
        fov_5_5_ctr = data[well][str(center_5_5)]["xy"]

        # Eliminate the coodinates of 3*3 fovs from all indexes
        for index in sorted(indexes, reverse=True):
            del all_index[index]

        all_index_5_5 = list(np.arange(68)) 
        indexes_5_5 = fov_5_5 + fov_3
        # Eliminate the coodinates of 5*5 and one 3*3 fov from all indexes
        for index in sorted(indexes_5_5, reverse=True):
            del all_index_5_5[index]
            
    
    
"""
