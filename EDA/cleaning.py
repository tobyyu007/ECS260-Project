import pandas as pd

# read repo.csv
df = pd.read_csv('data/Query_javascript/repo.csv')
print("Shape of repo.csv: ", df.shape)

# select the value contains 'javascript' in languages columns
df_javascript = df[df['languages'].str.contains('javascript', case=False, na=False)]
print("Shape of repo.csv contains javascript in Launguage column: ", df_javascript.shape)

# check if the dataframe contains any missing values in stars column
print("NA Value in Stars: ", df_javascript['stars'].isnull().sum())


# popularity = # stars + # forks + # pullRequests^2
# create a new column called 'popularity' with the formula
df_javascript['popularity'] = df_javascript['stars'] + df_javascript['forks'] + df_javascript['pullRequests'] ** 2

# sort the dataframe by the column 'popularity' with descending order
df_javascript = df_javascript.sort_values(by='popularity', ascending=False)

# print the rows of the df_javascript
print("Rows of the df_javascript", len(df_javascript))

# dump df_javascript to csv
df_javascript.to_csv('data/Query_javascript/repo_sorted.csv', index=False)

# Choose the top 167 repositories
df_javascript_top_167 = df_javascript.iloc[:168]
df_javascript_top_167.to_csv('data/Query_javascript/repo_top_167.csv', index=False)

# choose row from 168 to 334
df_javascript_168_to_334 = df_javascript.iloc[168:335]
df_javascript_168_to_334.to_csv('data/Query_javascript/repo_168_to_334.csv', index=False)

# choose row from 335 to 500
df_javascript_335_to_500 = df_javascript.iloc[335:500]
df_javascript_335_to_500.to_csv('data/Query_javascript/repo_335_500.csv', index=False)