from pydriller import Repository
import pandas as pd
from tqdm import tqdm
import subprocess
import os

# read csv from Data/Query_javascript/repo_168_to_334.csv
df = pd.read_csv('Data/Query_javascript/target_2.csv')

# convert the columns of url to a list
repo_urls = df['url'].tolist()
repo_names = df['name'].tolist()

# create a 'Repo' directory if not exists
if not os.path.exists('Repo'):
    os.makedirs('Repo')

# Directory where you want to clone the repositories
clone_dir = os.path.expanduser("./Repo")

# Check if the clone directory exists, if not, create it
os.makedirs(clone_dir, exist_ok=True)

# Change to the clone directory
os.chdir(clone_dir)

for repo_url, repo_name in tqdm(zip(repo_urls, repo_names), total=len(repo_urls), desc="Analyzing repositories"):
    # Clone the repository URLs 
    subprocess.run(["git", "clone", repo_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Print a message when all repositories have been cloned
    tqdm.write(str(repo_name) + " has been cloned")

    # Create a list to store commit data dictionaries
    commits_list = []

    # Traverse through the commits in the repository
    for commit in Repository(repo_name).traverse_commits():
        data = {
            'commit_hash': commit.hash,
            'author_name': commit.author.name,
            'author_date': commit.author_date,
            'author_timezone': commit.author_timezone,
            'committer_name': commit.committer.name,
            'commit_date': commit.committer_date,
            'commit_timezone': commit.committer_timezone,
            'commit_msg': commit.msg
        }
        # Append the commit data dictionary to the list
        commits_list.append(data)

    # Convert the list of dictionaries to a DataFrame
    commits = pd.DataFrame(commits_list)

    #print(commits.head())
    #print(commits.shape)

    # Dump commits to a CSV file
    commits.to_csv(repo_name + '_commits.csv', index=False)


    # get the list of modified files for each commit
    modified_files = []

    for commit in Repository(repo_name).traverse_commits():
        for modified_file in commit.modified_files:
            data = {
                'commit_hash': commit.hash,
                'author': commit.author.name,
                'modified_file': modified_file.filename,
                'change_type': modified_file.change_type.name,
                'complexity': modified_file.complexity
            }
            modified_files.append(data)

    # Convert the list of dictionaries to a DataFrame
    modified_files = pd.DataFrame(modified_files)

    tqdm.write(str(modified_files.head()))
    tqdm.write(str(modified_files.shape)+ '\n')

    # Dump modified files to a CSV file
    modified_files.to_csv(repo_name + '_modified_files.csv', index=False)

    # delete the cloned repository
    subprocess.run(["rm", "-rf", repo_name])