from pymongo import MongoClient
from pydriller import Repository
import requests
import time
import json
import os
import lizard


# connect to server
client = MongoClient("mongodb://localhost:27018/")  #change port number if needed (default for mongoDB is 27017)
# get database
db = client["GithubRepo"]
# get collection
raw_data_collection = db["JavaScript_60"]
documentation_data_collection = db["Documentation_Record"]
# get all repos' url
proj = {
    "name": True,
    "owner": True,
    "url": True,
    "popularity": True
}
repo_list = raw_data_collection.find(projection=proj)

for repo in repo_list:
    repo_name = repo["name"]
    repo_owner = repo["owner"]
    print("Processing repo: ", repo_name)
    
    # count change time of documentation
    change_count = 0
    commits = Repository("./Repo/"+repo_owner + "_" + repo_name, only_modifications_with_file_types=['.md','.txt']).traverse_commits()
    for c in commits:
        for f in c.modified_files:
            f_name = f.filename
            str_len = len(f_name)
            if (f_name[(str_len - 3):(str_len)] == ".md") or (f_name[(str_len - 4):(str_len)] == ".txt"):
                change_count += 1
                if change_count % 500 == 0:
                    print("now count: ", change_count)
    
    # count number of documentation and lines of documentation
    documentation_count = 0
    code_line_count = 0
    file_size_count = 0
    for root, dirs, files in os.walk("./Repo/"+repo_owner + "_" + repo_name):
        for f in files:
            str_len = len(f)
            if (f[(str_len - 3):(str_len)] == ".md") or (f[(str_len - 4):(str_len)] == ".txt"):
                documentation_count+=1
                code_line_count += lizard.analyze_file(root + "/"+f).nloc
                file_size_count += os.path.getsize(root + "/" + f)
        
    print(repo_name, ": ", documentation_count, " / ", code_line_count, " / ", change_count, " / ", file_size_count)
    
    # insert data into database
    doc = {
        "$set":{    
            "name": repo["name"],
            "owner": repo["owner"],
            "url": repo["url"],
            "popularity": repo["popularity"],
            "number_of_documentation": documentation_count,
            "lines_of_documentation": code_line_count,
            "changes_of_documentation": change_count,
            "filesize_of_documentation": file_size_count
        }
    }
    # documentation_data_collection.insert_one(doc)
    # documentation_data_collection.update_one(filter={"url":repo["url"]},update=doc)
    documentation_data_collection.update_one(filter={"url":repo["url"]},update=doc, upsert=True)