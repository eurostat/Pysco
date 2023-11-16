import pandas as pd

# Replace 'your_file.csv' with the actual path to your CSV file
file_path = '/home/juju/Bureau/gisco/grid_pop_c2021/NL_2021_0000_V0002.csv'

# Use read_csv with sep=';' to specify the semicolon as the separator
df = pd.read_csv(file_path, sep=';')

# Display the DataFrame
print(df)
