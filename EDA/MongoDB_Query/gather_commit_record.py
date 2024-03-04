from pymongo import MongoClient
from pydriller import Repository

client = MongoClient("mongodb://localhost:27018/") #change port number if needed (default for mongoDB is 27017)

# get database
db = client["GithubRepo"]

# get collection
raw_data_collection = db["JavaScript_60"]
commit_data_collection = db["Commit_Record"]

# get all repos' url
proj = {
    "url": True,
    "name": True,
    "owner": True
}
res = raw_data_collection.find(projection=proj)


batch_size = 3000
# get commit history from pydriller
for iter in res:
    print("Processing repo: ", iter["url"])    
    
    commits = Repository("./Repo/"+iter["owner"] + "_" + iter["name"]).traverse_commits()
    commit_total = 0
    
    
    commit_list = []
    for commit in commits:
        if commit_total % batch_size == 0:
            print(commit_total)
        c = {
        "repo_url": iter["url"],
        "repo_name": iter["name"],
        "repo_owner": iter["owner"],
        "hash": commit.hash,
        "msg": commit.msg,
        "author": commit.author.name,
        "committer": commit.committer.name,
        "author_date": commit.author_date,
        "author_timezone": commit.author_timezone,
        "committer_date": commit.committer_date,
        "committer_timezone": commit.committer_timezone
        }
        commit_list.append(c)
        commit_total+=1
        try:
            if commit_total % batch_size == 0:
                print("add data to database")
                commit_data_collection.insert_many(commit_list)
                commit_list = []
        except:
            print("error")
    
    # add rest of the records only when they are not added in the for loop
    if commit_total % batch_size != 0:
        commit_data_collection.insert_many(commit_list)