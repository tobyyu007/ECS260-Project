# setup connection to the database and test the connection
# on localhost:27017

from pymongo import MongoClient

import pandas as pd

# connect to the database
client = MongoClient('localhost', 27017)

# Connect to the 'GithubRepo' database
db = client['GithubRepo']

# List all the collections in the 'GithubRepo' database
print("All collections: ", db.list_collection_names())

# Connect to the 'Documentation_Record' collection
Documentation_Record = db['Documentation_Record']
print("Number of Records in Documentation_Record: ", Documentation_Record.count_documents({}))
print()

# print("Documentation_Record: ", Documentation_Record.find_one())
print("Documentation_Record: ")

# print all the records in the 'Documentation_Record' collection
# read the records in the 'Documentation_Record' collection into a pandas dataframe

# create a dataframe to store the records in the 'Documentation_Record' collection
df = pd.DataFrame(list(Documentation_Record.find()))
print(df)
print()

# seperate df into popular_df and unpopular_df
popular_df = df.iloc[:30]
unpopular_df = df.iloc[30:]
# popular_df = df[df['popularity'] == 'popular']
# unpopular_df = df[df['popularity'] == 'unpopular']

print("popular_df: ", popular_df)
print()
print("unpopular_df: ", unpopular_df)

# Connect to the 'reposInfo' collection
reposInfo = db['reposInfo']
print("reposInfo: ", reposInfo.find_one())

# Connect to the 'JavaScript_top500' collection
# JavaScript_top500 = db['JavaScript_top500']
# print(JavaScript_top500.find_one())

# Connect to the 'JavaScript_60' collection
JavaScript_60 = db['JavaScript_60']
print("JavaScript_60: ", JavaScript_60.find_one())