from pymongo import MongoClient
from pydriller import Repository
from tqdm import tqdm
import subprocess
import requests
import time
import json
import os


client = MongoClient("mongodb://localhost:27018/")

# get database
db = client["GithubRepo"]

# get collection
raw_data_collection = db["JavaScript_60"]

# get all repos' url
proj = {
    "name": True,
    "url": True,
    "owner": True
}

repo_list = raw_data_collection.find(projection=proj)

# create a 'Repo' directory if not exists
if not os.path.exists('Repo'):
    os.makedirs('Repo')
    
# Change to the clone directory
os.chdir('Repo')

for repo in tqdm(repo_list, desc="Analyzing repositories"):
    repo_url = repo["url"]
    repo_name = repo["name"]
    repo_owner = repo["owner"]
    # Clone the repository URLs 
    # if not os.path.exists(repo_name):
    if not repo_owner + "_" + repo_name in os.listdir("./"):
        subprocess.run(["git", "clone", repo_url, repo_owner + "_" + repo_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Print a message when all repositories have been cloned
    tqdm.write(str(repo_name) + " has been cloned")