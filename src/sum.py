import pandas as pd

# Load the CSV file
csv_file = "/home/juju/Bureau/Filosofi2019_carreaux_200m_gpkg./aaa.csv"
data = pd.read_csv(csv_file)

# Compute the sum of each column
column_sums = data.sum()

# Print the results
print("Sum of columns:")
print(column_sums)
