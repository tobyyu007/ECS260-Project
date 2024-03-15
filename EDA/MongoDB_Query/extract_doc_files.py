from pymongo import MongoClient
from pydriller import Repository
import requests
import time
import json
import os
import shutil


# connect to server
client = MongoClient("mongodb://localhost:27018/")
# get database
db = client["GithubRepo"]
# get collection
raw_data_collection = db["JavaScript_60"]

# get all repos' url
proj = {
    "name": True,
    "owner": True,
    "url": True,
    "popularity": True
}
repo_list = raw_data_collection.find(projection=proj)

if not os.path.exists('repo_doc_files'):
    os.makedirs('repo_doc_files')

base_working_dir = os.getcwd()
repo_doc_files_dir = "repo_doc_files"
repo_dir = "Repo"

for repo in repo_list:
    repo_name = repo["name"]
    repo_owner = repo["owner"]
    print("Processing repo: ", repo_name)
    
    if not repo_owner + "_" + repo_name in os.listdir(repo_doc_files_dir):
        os.makedirs(os.path.join(repo_doc_files_dir, repo_owner + "_" + repo_name))
    else:
        print("Repo " , repo_owner + "_" + repo_name , " has processed before")
        continue
    
    
    # switch current working to this repo
    os.chdir(os.path.join(repo_dir, repo_owner + "_" + repo_name))
    # go through all files in this repo
    for root, dirs, files in os.walk('.'):
        for f in files:
            str_len = len(f)
            if (f[(str_len - 3):(str_len)] == ".md") or (f[(str_len - 4):(str_len)] == ".txt") and (os.path.getsize(os.path.join(root, f)) >= 5):
                # print(os.path.exists(os.path.join(root, f)), "   ", os.getcwd(), "     ", root, "    ", f)
                shutil.copy(os.path.join(root, f), os.path.join(base_working_dir, repo_doc_files_dir, repo_owner + "_" + repo_name))
                os.chdir(os.path.join(base_working_dir, repo_doc_files_dir, repo_owner + "_" + repo_name))
                
                # in root dir
                if len(root) == 1:
                    os.rename(f, ('_' + f))
                # in child dir    
                elif len(root) > 1:
                    # ignore first char '.' and replace '\\' with '_' to represent path
                    os.rename(f, (root[1:] + f).replace("\\", "_"))
                
                # go back working directory after renaming file
                os.chdir(os.path.join(base_working_dir, repo_dir, repo_owner + "_" + repo_name))
                

    os.chdir(base_working_dir)
    print("end: ", repo_name)