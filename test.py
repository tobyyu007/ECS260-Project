import requests

owner = "marcius-studio"
name = "tradingview-jsapi-forex"
access_token = "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"

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
    try:
        if data.get('data') and data['data'].get('repository') and \
           data['data']['repository'].get('defaultBranchRef') and \
           data['data']['repository']['defaultBranchRef'].get('target') and \
           data['data']['repository']['defaultBranchRef']['target'].get('history'):
            commits_count = data['data']['repository']['defaultBranchRef']['target']['history']['totalCount']
            print(f"Repository {owner}/{name} has {commits_count} commits.")
            valid_response = True
        else:
            print(f"Invalid response structure for {owner}/{name}.")
    except Exception as e:
        print(f"Error processing data for {owner}/{name}: {e}")
else:
    tqdm.write(f"Failed to fetch data for {owner}/{name}, HTTP status {response.status_code}. Retrying in 60 seconds...")
    time.sleep(60)  # Wait for 60 seconds before retrying
data = response.json()

# commits_count = data['data']['repository']['defaultBranchRef']['target']['history']['totalCount']
# print(f"Number of commits: {commits_count}")