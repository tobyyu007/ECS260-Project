from pymongo import MongoClient
from datetime import datetime
import os

client = MongoClient("mongodb://localhost:27018/")

# get database
db = client["GithubRepo"]

# get collection
raw_data_collection = db["JavaScript_60"]
doc_collection = db["Documentation_Record"]
code_quality_collection = db["CodeQuality_Record"]
time_zone_collection = db["Timezone_Record"]




# add popularity tag
# query = {
#     "popularity": {"$gt": 1000},
# }
# raw_data_collection.update_many(query, update={
#     '$set': {'popular_level': "high"}
# })
# query = {
#     "popularity": {"$lt": 1000},
# }
# raw_data_collection.update_many(query, update={
#     '$set': {'popular_level': "low"}
# })



# delete a field
# raw_data_collection.update_many({}, update={
#     '$unset': {'popularity_classification': 1}
# })



# check license
filter_criteria = {"license": {"$exists": True}}
repos = raw_data_collection.find(filter_criteria)
doc_collection.update_many(filter={}, update={"$set":{"has_license":False}})
has_license_list = []
for repo in repos:
    has_license_list.append(repo["url"])
doc_collection.update_many(filter={"url":{"$in":has_license_list}}, update={"$set":{"has_license":True}})



# calculate project age
proj={
    "url":True,
    "createdAt": True
}
repo_list = raw_data_collection.find({}, proj)
for repo in repo_list:
    repo_age_in_days = (datetime(2024, 2, 1) - repo["createdAt"]).days
    query = {
        "url":repo["url"]
    }
    update_doc = {
        "$set":{
            "repo_age":repo_age_in_days 
        }
    }
    doc_collection.update_one(query, update_doc)
    code_quality_collection.update_one(query, update_doc)
    time_zone_collection.update_one(query, update_doc)



# calculate project size
proj={
    "name": True,
    "owner": True,
    "url":True,
}
repo_list = raw_data_collection.find({}, proj)
for repo in repo_list:
    
    repo_name = repo["name"]
    repo_owner = repo["owner"]
    print("Processing repo: ", repo_name)
    
    project_sz = 0
    for root, dirs, files in os.walk("./Repo/"+repo_owner + "_" + repo_name):
        for f in files:
            project_sz += os.path.getsize(os.path.join(root, f))
            
    print(repo_name, ": ", project_sz)
    project_sz = int(project_sz / 1000)
    query = {
        "url":repo["url"]
    }
    update_doc = {
        "$set":{
            "repo_size":project_sz 
        }
    }
    doc_collection.update_one(query, update_doc)
    code_quality_collection.update_one(query, update_doc)
    time_zone_collection.update_one(query, update_doc)



# add team size
proj={
    "url":True,
    "users": True,
}
repo_list = raw_data_collection.find({}, proj)
for repo in repo_list:
    query = {
        "url":repo["url"]
    }
    update_doc = {
        "$set":{
            "team_size":repo["users"] 
        }
    }
    doc_collection.update_one(query, update_doc)
    code_quality_collection.update_one(query, update_doc)
    time_zone_collection.update_one(query, update_doc)



# compute code quality
repo_list = raw_data_collection.find({})
for repo in repo_list:
    query = {
        "url":repo["url"]
    }
    old_doc = code_quality_collection.find_one(query)
    print(repo["url"])
    update_doc = {
        "$set":{
            "code_smell_per_loc": old_doc["code_smell"] / old_doc["ncloc"],
            "cognitive_complexity_per_loc": old_doc["cognitive_complexity"] / old_doc["ncloc"],
            "bug_pronesses": old_doc["bugCount"] / repo["commits"]
        }
    }
    code_quality_collection.update_one(query, update_doc)