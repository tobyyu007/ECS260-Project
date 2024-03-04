from pymongo import MongoClient

# connect to server
client = MongoClient("mongodb://localhost:27018/")  #change port number if needed (default for mongoDB is 27017)
# get database
db = client["GithubRepo"]
# get collection
raw_data_collection = db["JavaScript_60"]
commit_data_collection = db["Commit_Record"]
timezone_data_collection = db["Timezone_Record"]

# get all repos' url
proj = {
    "name": True,
    "owner": True,
    "url": True,
    "popularity": True,
    "popular_level": True,
    "languages": True
}
repo_list = raw_data_collection.find(projection=proj)

for repo in repo_list:
    repo_name = repo["name"]
    repo_owner = repo["owner"]
    repo_url = repo["url"]
    repo_languages = repo["languages"]
    print("Processing repo: ", repo_name)
    
    committer_tz_res = commit_data_collection.aggregate([{"$match":{"repo_url":repo_url}},
                                                           {"$group":{"_id": "$committer_timezone", "count": {"$sum": 1}}}])
    author_tz_res = commit_data_collection.aggregate([{"$match":{"repo_url":repo_url}},
                                                           {"$group":{"_id": "$author_timezone", "count": {"$sum": 1}}}])
    
    committer_timezones = list()
    author_timezones = list()
    
    for x, y in zip(committer_tz_res, author_tz_res):
        committer_timezones.append({
            "timezone": x["_id"],
            "count": x["count"]
        })
        author_timezones.append({
            "timezone": y["_id"],
            "count": y["count"]
        })
    
    repo_languages_list = repo_languages.split(',')
    
    doc = {
        "name": repo["name"],
        "owner": repo["owner"],
        "url": repo["url"],
        "popularity": repo["popularity"],
        "popular_level": repo["popular_level"],
        "committer_timezones": committer_timezones,
        "author_timezones": author_timezones,
        "committer_timezone_count":len(committer_timezones),
        "author_timezone_count":len(author_timezones),
        "languages": repo_languages_list,
        "languages_count": len(repo_languages_list)
    }
    timezone_data_collection.insert_one(doc)