import csv
import requests
import time

url = "https://api.github.com/search/repositories"

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": "Bearer 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",
    "X-GitHub-Api-Version": "2022-11-28"
}

# Function to flatten the repository data
def flatten_repo(repo):
    flat_repo = {}
    for key, value in repo.items():
        if isinstance(value, dict):
            # For nested dictionaries, prefix key with parent key
            for sub_key, sub_value in value.items():
                flat_repo[f"{key}_{sub_key}"] = sub_value
        else:
            flat_repo[key] = value
    return flat_repo

# Process the first few pages to determine all possible columns
all_keys = set()
for page in range(1, 2):
    response = requests.get(url, headers=headers, params={"q": "javascript", "per_page": 100, "page": page})
    sample_data = response.json()
    for repo in sample_data['items']:
        all_keys.update(flatten_repo(repo).keys())

# Open a file to write the CSV data
with open('github_repositories_full.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=all_keys)
    writer.writeheader()  # Write the header

    for page in range(1, 2):
        params = {
            "q": "javascript",
            "type": "repositories",
            "order": "desc",
            "per_page": 100,
            "page": page
        }
        
        response = requests.get(url, headers=headers, params=params)
        while response.status_code != 200:
            print("Failed to fetch repositories. Retrying in 1 minute...")
            response = requests.get(url, headers=headers, params=params)
            time.sleep(60)
        
        data = response.json()
        
        # Write each repository data to the CSV file
        for repo in data.get('items', []):
            flattened_repo = flatten_repo(repo)
            # Fill in missing keys with 'N/A' or some default value
            for key in all_keys:
                flattened_repo.setdefault(key, 'N/A')
            writer.writerow(flattened_repo)
