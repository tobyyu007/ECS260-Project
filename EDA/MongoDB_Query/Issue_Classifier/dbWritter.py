#Import all the required libraries
from pymongo import MongoClient
import csv
print("Import Complete.....................")

client = MongoClient('localhost', 27017)
db = client['GithubRepo']
codeQuality = db['CodeQuality_Record']
print("Mongo Setup Complete.....................")

# CSV file processing
print("Writting to MongoDB.....................")
filename = 'repo_bug_counts.csv'  # Your CSV file name
with open(filename, 'r') as csvfile:
    csvreader = csv.DictReader(csvfile) 
    for row in csvreader:
        repo_url = row['repo_url']
        bug_count = row['bugCount']
        # Update the MongoDB document
        codeQuality.update_one({'url': repo_url}, {'$set': {'bugCount': int(bug_count)}}, upsert=False)
print("Complete.....................")