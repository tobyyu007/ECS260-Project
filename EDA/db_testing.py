# setup connection to the database and test the connection
# on localhost:27017

from pymongo import MongoClient

# connect to the database
client = MongoClient('localhost', 27017)

# Connect to the 'GithubRepo' database
db = client['GithubRepo']

# List all the collections in the 'GithubRepo' database
print(db.list_collection_names())

# Connect to the 'Documentation_Record' collection
Documentation_Record = db['Documentation_Record']
print(Documentation_Record.find_one())

# Connect to the 'reposInfo' collection
reposInfo = db['reposInfo']
print(reposInfo.find_one())

# Connect to the 'JavaScript_top500' collection
# JavaScript_top500 = db['JavaScript_top500']
# print(JavaScript_top500.find_one())