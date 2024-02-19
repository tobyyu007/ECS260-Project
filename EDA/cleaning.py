import pandas as pd

# read repo.csv
df = pd.read_csv('data/Query_javascript/repo.csv')
print("Shape of repo.csv: ", df.shape)

# select the value contains 'javascript' in languages columns
df_javascript = df[df['primaryLanguage'].str.contains('JavaScript', case=False, na=False)]
print("Shape of repo.csv contains javascript as Primary Launguage column: ", df_javascript.shape)

# check if the dataframe contains any missing values in stars column
print("Number of NA Value in Stars column: ", df_javascript['stars'].isnull().sum())

# filter out repo less than 5 stars
df_javascript = df_javascript[df_javascript['stars'] >= 5]
print("Shape of repo.csv contains javascript in Launguage column and stars >= 5: ", df_javascript.shape)

# popularity = # stars + # forks + # pullRequests^2
# create a new column called 'popularity' with the formula
df_javascript['popularity'] = df_javascript['stars'] + df_javascript['forks'] + df_javascript['pullRequests'] ** 2

# sort the dataframe by the column 'popularity' with descending order
df_javascript = df_javascript.sort_values(by='popularity', ascending=False)

# dump df to csv
df_javascript.to_csv('data/Query_javascript/repo_clean.csv', index=False)

print(df_javascript.shape)
print(df_javascript.head(5))

# split df_javascript into 2 parts for parallel processing
df_javascript_1 = df_javascript.iloc[:27336]
# df_javascript_1.to_csv('data/Query_javascript/target_1.csv', index=False)
print("Shape of df_javascript_1: ", df_javascript_1.shape)

df_javascript_2 = df_javascript.iloc[27336:]
# df_javascript_2.to_csv('data/Query_javascript/target_2.csv', index=False)
print("Shape of df_javascript_2: ", df_javascript_2.shape)

# Go to get_num_commits.py to get the number of commits for each repository
# get_num_commits.py will write the commit for each repo back to target_1.csv and target_2.csv
# combine target_1.csv and target_2.csv to generate repo_with_num_commits.csv

# read repo_with_num_commits.csv to see if the repo's commit is less than 30
df = pd.read_csv('data/Query_javascript/repo_with_num_commits.csv')
print("Shape of repo_with_num_commits.csv: ", df.shape)

# check NA value in commits column
print("Number of NA Value in commits column: ", df['commits'].isnull().sum())

# filter out repo less than 30 commits
df = df[df['commits'] >= 30]
print("Shape of repo_with_num_commits.csv contains commits >= 30: ", df.shape)

# dump df to csv
df.to_csv('data/Query_javascript/repo_clean.csv', index=False)

# Go to LDA/script.py to get the domain of each repository
# script.py will write the domain for each repo back to repo_with_num_commits.csv
# script.py will add a new column called 'isApp' in repo_clean.csv

# read repo_clean.csv
df = pd.read_csv('data/Query_javascript/repo_clean.csv')

# print df.shape
print(df.shape)

# print the True and False count of the column of isApp
print(df['isApp'].value_counts())

# select the isApp is True
df = df[df['isApp'] == True]

print(df.shape)

# sort the dataframe by the column 'popularity' with descending order
df = df.sort_values(by='popularity', ascending=False)

print("head: ")
print(df.head(5))

print("tail: ")
print(df.tail(5))

# take the first 30 rows of the dataframe and dump to csv
df.head(30).to_csv('data/Query_javascript/js_popular.csv', index=False)

# take the last 30 rows of the dataframe and dump to csv
df.tail(30).to_csv('data/Query_javascript/js_unpopular.csv', index=False)