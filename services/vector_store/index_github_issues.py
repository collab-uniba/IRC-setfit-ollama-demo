#!/usr/bin/env python3
"""
Utility script for batch indexing GitHub issues from the GitHub API.

Usage:
    python index_github_issues.py --owner pytorch --repo pytorch --token $GITHUB_TOKEN --max-issues 5000
"""

import argparse
import requests
import time
import logging
from typing import List, Dict, Optional
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_github_issues(
    owner: str,
    repo: str,
    token: Optional[str] = None,
    max_issues: int = 1000,
    state: str = "all"
) -> List[Dict]:
    """
    Fetch issues from GitHub's REST API.
    
    Args:
        owner: Repository owner
        repo: Repository name
        token: GitHub personal access token (optional but recommended for rate limits)
        max_issues: Maximum number of issues to fetch
        state: Issue state filter (open, closed, all)
        
    Returns:
        List of issue dictionaries
    """
    base_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    
    issues = []
    page = 1
    per_page = 100
    
    logger.info(f"Fetching issues from {owner}/{repo}...")
    
    while len(issues) < max_issues:
        params = {
            "state": state,
            "page": page,
            "per_page": per_page,
            "sort": "created",
            "direction": "desc"
        }
        
        try:
            response = requests.get(base_url, headers=headers, params=params)
            
            # Check rate limit
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            if remaining < 10:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(reset_time - time.time(), 0) + 1
                logger.warning(f"Rate limit low ({remaining}), waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            
            page_issues = response.json()
            
            if not page_issues:
                break
            
            # Filter out pull requests
            page_issues = [issue for issue in page_issues if 'pull_request' not in issue]
            
            issues.extend(page_issues)
            
            logger.info(f"Fetched {len(issues)} issues so far...")
            
            page += 1
            
            # Small delay to be nice to the API
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issues: {str(e)}")
            break
    
    issues = issues[:max_issues]
    logger.info(f"Fetched {len(issues)} total issues")
    
    return issues


def transform_github_issues(github_issues: List[Dict]) -> List[Dict]:
    """
    Transform GitHub API issue format to our vector store format.
    
    Args:
        github_issues: Raw issues from GitHub API
        
    Returns:
        Transformed issues ready for indexing
    """
    transformed = []
    
    for issue in github_issues:
        transformed_issue = {
            "id": f"github-{issue['number']}",
            "title": issue['title'],
            "body": issue.get('body', '') or '',
            "labels": [label['name'] for label in issue.get('labels', [])],
            "state": issue['state'],
            "created_at": issue['created_at'],
            "metadata": {
                "number": issue['number'],
                "url": issue['html_url'],
                "user": issue['user']['login'],
                "comments": issue.get('comments', 0)
            }
        }
        transformed.append(transformed_issue)
    
    return transformed


def index_issues_to_vector_store(
    issues: List[Dict],
    vector_store_url: str,
    batch_size: int = 50
):
    """
    Index issues to the vector store API.
    
    Args:
        issues: List of issues to index
        vector_store_url: Base URL of the vector store API
        batch_size: Number of issues to send per request
    """
    index_url = f"{vector_store_url}/index"
    
    total_indexed = 0
    
    for i in range(0, len(issues), batch_size):
        batch = issues[i:i + batch_size]
        
        try:
            response = requests.post(
                index_url,
                json={"issues": batch},
                timeout=30
            )
            response.raise_for_status()
            
            total_indexed += len(batch)
            logger.info(f"Indexed {total_indexed}/{len(issues)} issues")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error indexing batch: {str(e)}")
            continue
    
    logger.info(f"Indexing complete: {total_indexed} issues indexed")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and index GitHub issues into vector store"
    )
    parser.add_argument(
        "--owner",
        required=True,
        help="Repository owner"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository name"
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (recommended)"
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=1000,
        help="Maximum number of issues to fetch (default: 1000)"
    )
    parser.add_argument(
        "--state",
        choices=["open", "closed", "all"],
        default="all",
        help="Issue state filter (default: all)"
    )
    parser.add_argument(
        "--vector-store-url",
        default="http://localhost:8001",
        help="Vector store API URL (default: http://localhost:8001)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for indexing (default: 50)"
    )
    
    args = parser.parse_args()
    
    try:
        # Fetch issues from GitHub
        github_issues = fetch_github_issues(
            owner=args.owner,
            repo=args.repo,
            token=args.token,
            max_issues=args.max_issues,
            state=args.state
        )
        
        if not github_issues:
            logger.warning("No issues fetched, exiting")
            return
        
        # Transform to our format
        issues = transform_github_issues(github_issues)
        
        # Index to vector store
        index_issues_to_vector_store(
            issues=issues,
            vector_store_url=args.vector_store_url,
            batch_size=args.batch_size
        )
        
        logger.info("Process completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
