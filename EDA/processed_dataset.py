import pandas as pd

# Read in the data
df_2008_2014 = pd.read_csv('data/Query_javascript/2008-01-01 to 2014-12-31 (Remove unusual line terminators).csv')
df_2015_2017 = pd.read_csv('data/Query_javascript/2015-01-01 to 2017-12-31.csv')
df_2018_01_2018_11 = pd.read_csv('data/Query_javascript/2018-01-01 to 2018-11-22.csv')
df_2018_11_2019_03 = pd.read_csv('data/Query_javascript/2018-11-23 to 2019-03-25.csv')
df_2019_03_2019_12 = pd.read_csv('data/Query_javascript/2019-03-26 to 2019-12-31.csv')
df_2020_01_2021_12 = pd.read_csv('data/Query_javascript/2020-01-01 to 2021-12-31.csv')
df_2022_01_2022_12 = pd.read_csv('data/Query_javascript/2022-01-01 to 2022-12-31.csv')
df_2023_01_01_2023_01_14 = pd.read_csv('data/Query_javascript/2023-01-01 to 2023-01-14.csv')
df_2023_01_2023_03 = pd.read_csv('data/Query_javascript/2023-01-15 to 2023-03-26.csv')
df_2023_03_2024_01 = pd.read_csv('data/Query_javascript/2023-03-27 to 2024-01-30.csv')


print(df_2008_2014.shape)
print(df_2015_2017.shape)
print(df_2018_01_2018_11.shape)
print(df_2018_11_2019_03.shape)
print(df_2019_03_2019_12.shape)
print(df_2020_01_2021_12.shape)
print(df_2022_01_2022_12.shape)
print(df_2023_01_01_2023_01_14.shape)
print(df_2023_01_2023_03.shape)
print(df_2023_03_2024_01.shape)
print()

# Concatenate the dataframes
df = pd.concat([df_2008_2014, df_2015_2017, df_2018_01_2018_11, df_2018_11_2019_03, df_2019_03_2019_12, df_2020_01_2021_12, df_2022_01_2022_12, df_2023_01_01_2023_01_14, df_2023_01_2023_03, df_2023_03_2024_01])
print(df.shape)

# dump the dataframe to a csv file
df.to_csv('data/Query_javascript/repo.csv', index=False)