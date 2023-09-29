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
TARGET_REPO_COUNT = 100

headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"Bearer {os.getenv('GITHUB_PAT')}"
}

# Prepare the initial search query
query = f"language:{LANGUAGE} stars:>{MIN_STARS} forks:>{MIN_FORKS} archived:false"

params = {
    "q": query,
    "sort": "size",  # Sort by size in descending order
    "order": "desc",
    "per_page": PER_PAGE,
    "page": 1
}

filtered_repos = []

base_url = 'https://api.github.com'

def commitCount(u, r):
    print(f"https://github.com/{u}/{r}", flush=True)
    while True:
        try:
            response = requests.get('https://api.github.com/repos/{}/{}/commits?per_page=1'.format(u, r), headers=headers, timeout=3)
            break
        except:
            pass
    return re.search('\d+$', response.links['last']['url']).group()

while len(filtered_repos) < TARGET_REPO_COUNT:
    print(f"Fetching page {params['page']} from GitHub...")
    response = requests.get(GITHUB_API_URL, headers=headers, params=params)

    if response.status_code != 200:
        print("Error fetching repositories. Exiting.")
        break

    repos = response.json()["items"]

    for repo in repos:
        commits_url = repo["commits_url"].split("{")[0]
        
        commit_count = commitCount(repo['owner']['login'], repo['name'])

        if int(commit_count) >= MIN_COMMITS:
            filtered_repos.append({
                "name": repo["name"],
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "commits": commit_count,
                "size": repo["size"]  # Include the size of the repo
            })


        if len(filtered_repos) == TARGET_REPO_COUNT:
            break
    params["page"] += 1

# Save the filtered repositories to a CSV file
with open('filtered_repositories.csv', 'w', newline='') as csvfile:
    fieldnames = ["name", "url", "stars", "forks","commits", "size"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for repo in filtered_repos:
        writer.writerow(repo)

print(f"Filtered {len(filtered_repos)} repositories and saved to 'filtered_repositories.csv'")
