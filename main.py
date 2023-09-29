import requests
import csv

# Parameters
LANGUAGE = "javascript"
MIN_COMMITS = 10
MIN_STARS = 10
MIN_FORKS = 10
PER_PAGE = 100
GITHUB_API_URL = "https://api.github.com/search/repositories"
TARGET_REPO_COUNT = 100

headers = {
    "Accept": "application/vnd.github.v3+json"
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

while len(filtered_repos) < TARGET_REPO_COUNT:
    print(f"Fetching page {params['page']} from GitHub...")
    response = requests.get(GITHUB_API_URL, headers=headers, params=params)

    if response.status_code != 200:
        print("Error fetching repositories. Exiting.")
        break

    repos = response.json()["items"]

    for repo in repos:
        commits_url = repo["commits_url"].split("{")[0]
        # contributors_url = repo["contributors_url"]
        # response_contributors = requests.get(contributors_url, headers=headers)
        
        # if response_contributors.status_code == 200:
        #     contributors = response_contributors.json()
        #     commit_count = sum(contributor.get("contributions", 0) for contributor in contributors)
        # else:
        #     commit_count = 0
            # commit_count = len(requests.get(commits_url, headers=headers).json())
        
        main_branch_url = f"https://api.github.com/repos/{repo['owner']['login']}/{repo['name']}/branches/{repo['default_branch']}"
        response_branch = requests.get(main_branch_url, headers=headers)

        print(response_branch.json())
        
        if response_branch.status_code == 200:
            branch_data = response_branch.json()
            commit_count = branch_data['commit']['commit_count'] if 'commit_count' in branch_data['commit'] else 0
        else:
            commit_count = 0 

        print(commit_count)
        break

        if commit_count >= MIN_COMMITS:
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
