import requests
import pandas as pd
from tqdm import tqdm
import time

# access_token = "Your access token here"
access_token = "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"

# read csv
df = pd.read_csv('Data/Query_javascript/target_2.csv')

# convert the columns of url to a list
owners = df['owner'].tolist()
names = df['name'].tolist()

for owner, name in tqdm(zip(owners, names), total=len(names), desc="Analyzing repositories"):
    valid_response = False
    while not valid_response:
        query = f'''
        {{
        repository(owner: "{owner}", name: "{name}") {{
            defaultBranchRef {{
            target {{
                ... on Commit {{
                history(first: 0) {{
                    totalCount
                }}
                }}
            }}
            }}
        }}
        }}
        '''

        headers = {'Authorization': f'Bearer {access_token}'}
        url = 'https://api.github.com/graphql'

        response = requests.post(url, json={'query': query}, headers=headers)
        
        if response.status_code == 200:  # Check if the response is successful
            data = response.json()
            if data.get('data') and data['data'].get('repository') and \
                data['data']['repository'].get('defaultBranchRef') and \
                data['data']['repository']['defaultBranchRef'].get('target') and \
                data['data']['repository']['defaultBranchRef']['target'].get('history'):
                    commits_count = int(data['data']['repository']['defaultBranchRef']['target']['history']['totalCount'])
                    df.loc[(df['owner'] == owner) & (df['name'] == name), 'commits'] = commits_count
                    tqdm.write(f"Repository {owner}/{name} has {commits_count} commits.")
                    valid_response = True
            else:
                tqdm.write(f"Invalid response structure for {owner}/{name}.")
                break
        else:
            tqdm.write(f"Failed to fetch data for {owner}/{name}, HTTP status {response.status_code}. Retrying in 60 seconds...")
            time.sleep(60)  # Wait for 60 seconds before retrying

    # Optionally, write the updated DataFrame to a CSV file after each successful data fetch
    df.to_csv('Data/Query_javascript/target_2.csv', index=False)