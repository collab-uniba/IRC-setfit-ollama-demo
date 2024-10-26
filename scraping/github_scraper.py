from typing import List
from github import Github
from loguru import logger
from issue.issue import Issue

def validate_github_url(url: str) -> bool:
    """
    Uses GitHub API to validate the URL, for both issue and repository URLs
    """
    g = Github()
    try:
        if "issues" in url and url.split("/")[-1].isdigit():
            issue = g.get_repo(url).get_issue(int(url.split("/")[-1]))
        else:
            org_name = url.split("/")[3]
            repo_name = url.split("/")[4]
            repo = g.get_repo(f"{org_name}/{repo_name}")
    except Exception:
        return False

    return True


def scrape_github_issues(url: str, num_issues: int = 5, state: str = 'all') -> List[str]:
    """
    Scrapes GitHub issues from an URL
    If the url is a repository URL, it will scrape the issues from the repository
    If the url is an issue URL, it will scrape the issue details
    """
    # Initialize the Github object
    g = Github()

    org_name = url.split("/")[3]
    repo_name = url.split("/")[4]

    # Check if the URL is an issue URL
    if "issues" in url and url.split("/")[-1].isdigit():
        return scrape_single_issue(url, g, org_name, repo_name)
    # Scrape the issues and return the latest num_issues issues
    return scrape_multiple_issues(g, org_name, repo_name, num_issues, state)

def scrape_multiple_issues(g, org_name, repo_name, num_issues, state):
    repo = g.get_repo(f"{org_name}/{repo_name}")
    issues = repo.get_issues(state=state, sort='created', direction='desc')
    return [
        Issue(issue.title, issue.body, issue.html_url)
        for issue in issues[:num_issues]
    ]

def scrape_single_issue(url, g, org_name, repo_name):
    logger.info(f"Scraping issue from {url}")
    issue_number = int(url.split("/")[-1])

    repo = g.get_repo(f"{org_name}/{repo_name}")
    issue = repo.get_issue(issue_number)
    url = issue.html_url
    return Issue(issue.title, issue.body, url)

if __name__ == "__main__":
    url = "https://github.com/PyGithub/PyGithub/issues/3064"
    issues = scrape_github_issues(url)
    for issue in issues:
        print(issue)
    