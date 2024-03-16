# Import all the required libraries 
import re
import string
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pymongo import MongoClient
import csv
print("Import Complete.....................")

#Setup MongoDB client
client = MongoClient('localhost', 27017)
db = client['GithubRepo']
print("Mongo Setup Complete.....................")

#Text Cleaning
def text_cleaner(text:str)->str:
    text = text.lower()
    text = re.sub('\[.*?\]', '', text)
    text = re.sub('https?://\S+|www\.\S+', '', text)
    text = re.sub('<.*?>+', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\n', '', text)
    text = re.sub('\w*\d\w*', '', text)
    return text

#Predicting Issue Type
def prediction(text:str, class_names:list, tokenizer, model):
    # Tokenize and encode text for DistilBERT input
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)

    # Predict using the fine-tuned model
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = outputs.logits

    # Convert predictions to class names
    predicted_class_id = predictions.argmax().item()
    predicted_class_name = class_names[predicted_class_id]
    return predicted_class_name


#Define Model and Classes
print("Defining Model.....................")
tokenizer = AutoTokenizer.from_pretrained("AntoineMC/distilbart-mnli-github-issues")
model = AutoModelForSequenceClassification.from_pretrained("AntoineMC/distilbart-mnli-github-issues")
class_names = ["bug", "fearure", "question"]

#Define CSV File
print("Creating CSV File.....................")
output_file = 'repo_bug_counts.csv'
        
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    # Write the header row
    writer.writerow(['repo_url', 'bugCount'])

    # Get a list of all repo URLs
    repo_data = db['JavaScript_60']
    proj = {"msg": True}
    print("Getting All repo URLs.....................")
    all_repos = list(repo_data.find({}, {'url': 1}))
    repo_url = [repo['url'] for repo in all_repos]

    # Predict Issue Type and write to CSV
    for url in repo_url:
        print("Starting Prediction.....................")
        bugCount = 0
        query = {"repo_url": url}
        commit_list = db['Commit_Record'].find(filter=query, projection=proj)
        for commit in commit_list:
            text = text_cleaner(commit["msg"])
            issueType = prediction(text, class_names, tokenizer, model)
            if issueType == "bug":
                bugCount += 1
        # Write each repo's URL and bug count as a new row in the CSV
        print("Writting to file.....................")
        writer.writerow([url, bugCount])
        print("Done.....................")

print(f'Data written to {output_file}')