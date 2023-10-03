import requests
import csv
import re
import os
from dotenv import load_dotenv

load_dotenv()

# Parameters
LANGUAGE = "javascript"
MIN_COMMITS = 10
MIN_STARS = 10
MIN_FORKS = 10
PER_PAGE = 100
GITHUB_API_URL = "https://api.github.com/search/repositories"
TARGET_REPO_COUNT = 110

headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"Bearer {os.getenv('GITHUB_PAT')}"
}

# Prepare the initial search query
query = f"language:{LANGUAGE} stars:>{MIN_STARS} forks:>{MIN_FORKS} archived:false"

params = {
    "q": query,
    "sort": "size",
    "order": "desc",
    "per_page": PER_PAGE,
    "page": 1
}

filtered_repos = []

def commitCount(u, r):
    while True:
        try:
            response = requests.get(f'https://api.github.com/repos/{u}/{r}/commits?per_page=1', headers=headers, timeout=3)
            break
        except:
            pass
    return re.search('\d+$', response.links['last']['url']).group()

def is_dataset_repo(repo):
    keywords = ["dataset", "data-set", "data"]
    description = repo["description"] if repo["description"] else ""
    for keyword in keywords:
        if keyword in description.lower() or keyword in repo["name"].lower():
            return True
    return False

def is_majority_language_javascript(owner, repo_name):
    response = requests.get(f'https://api.github.com/repos/{owner}/{repo_name}/languages', headers=headers)
    if response.status_code == 200:
        languages = response.json()
        total_bytes = sum(languages.values())
        if "JavaScript" in languages:
            js_bytes = languages["JavaScript"]
            return (js_bytes / total_bytes) * 100 >= 50
    return False

while len(filtered_repos) < TARGET_REPO_COUNT:
    response = requests.get(GITHUB_API_URL, headers=headers, params=params)

    if response.status_code != 200:
        print("Error fetching repositories. Exiting.")
        break

    repos = response.json()["items"]

    for repo in repos:
        owner = repo['owner']['login']
        repo_name = repo['name']

        # Check if repo is a dataset repository
        if is_dataset_repo(repo):
            print(f"Repository {repo_name} is a dataset repository. Filtering out.")
            print(repo['html_url'])
            continue

        # Check if majority of the code is in JavaScript
        if not is_majority_language_javascript(owner, repo_name):
            print(f"Repository {repo_name} does not have a majority of its code in JavaScript. Filtering out.")
            print(repo['html_url'])
            continue

        commit_count = commitCount(owner, repo_name)

        if int(commit_count) >= MIN_COMMITS:
            filtered_repos.append({
                "name": repo_name,
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "commits": commit_count,
                "size": repo["size"]
            })
            print(f"Repository {repo_name} is OK.")

        if len(filtered_repos) == TARGET_REPO_COUNT:
            break

    params["page"] += 1

# Save the filtered repositories to a CSV file
with open('filtered_repositories.csv', 'w', newline='') as csvfile:
    fieldnames = ["name", "url", "stars", "forks", "commits", "size"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for repo in filtered_repos:
        writer.writerow(repo)

print(f"Filtered {len(filtered_repos)} repositories and saved to 'filtered_repositories.csv'")
