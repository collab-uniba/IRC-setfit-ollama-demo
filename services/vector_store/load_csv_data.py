"""
CSV Data Loading Module for Vector Store Service

This module handles loading and parsing GitHub issue data from CSV files
in the data directory.
"""

import pandas as pd
import glob
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def generate_id_from_url(url: str) -> str:
    """
    Generate a deterministic ID from a GitHub issue URL.
    
    Args:
        url: GitHub issue URL
        
    Returns:
        A 16-character hexadecimal ID
    """
    return hashlib.md5(url.encode()).hexdigest()[:16]


def parse_labels(label_str: Optional[str]) -> List[str]:
    """
    Parse label string into list of labels.
    Handles both single labels and comma-separated multiple labels.
    
    Args:
        label_str: String containing one or more labels
        
    Returns:
        List of label strings
    """
    if pd.isna(label_str) or not label_str or label_str.strip() == "":
        return []
    
    # Split by comma and strip whitespace from each label
    labels = [label.strip() for label in str(label_str).split(",")]
    
    # Filter out empty strings
    return [label for label in labels if label]


def load_issues_from_csv(data_dir: str) -> List[Dict]:
    """
    Load all issues from CSV files in the data directory.
    
    Expected CSV schema:
        - title: Issue title (string)
        - body: Issue description/body text (string)
        - label: Issue label(s) - single or comma-separated (string)
        - url: GitHub URL of the issue (string)
    
    Args:
        data_dir: Path to directory containing CSV files
        
    Returns:
        List of issue dictionaries ready for indexing
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return []
    
    csv_files = list(data_path.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {data_dir}")
        return []
    
    logger.info(f"Found {len(csv_files)} CSV file(s) to process")
    
    all_issues = []
    total_errors = 0
    
    for csv_file in csv_files:
        logger.info(f"Processing file: {csv_file.name}")
        
        try:
            # Try UTF-8 encoding first
            try:
                df = pd.read_csv(
                    csv_file,
                    encoding='utf-8',
                    on_bad_lines='warn'  # Log problematic lines but continue
                )
            except UnicodeDecodeError:
                # Fallback to latin-1 if UTF-8 fails
                logger.warning(f"UTF-8 decoding failed for {csv_file.name}, trying latin-1")
                df = pd.read_csv(
                    csv_file,
                    encoding='latin-1',
                    on_bad_lines='warn'
                )
            
            # Validate required columns
            required_columns = {'title', 'body', 'label', 'url'}
            missing_columns = required_columns - set(df.columns)
            
            if missing_columns:
                logger.error(
                    f"File {csv_file.name} is missing required columns: {missing_columns}. Skipping."
                )
                continue
            
            file_errors = 0
            file_issues = []
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    # Skip rows with missing critical fields
                    if pd.isna(row['title']) or pd.isna(row['url']):
                        logger.warning(
                            f"Row {idx + 1} in {csv_file.name} missing title or url. Skipping."
                        )
                        file_errors += 1
                        continue
                    
                    # Generate ID from URL
                    issue_id = generate_id_from_url(str(row['url']))
                    
                    # Parse labels
                    labels = parse_labels(row['label'])
                    
                    # Handle missing body
                    body = str(row['body']) if not pd.isna(row['body']) else ""
                    
                    issue = {
                        'id': issue_id,
                        'title': str(row['title']),
                        'body': body,
                        'labels': labels,
                        'state': 'open',  # Default to open since CSV doesn't specify
                        'created_at': None,  # Not available in CSV
                        'metadata': {
                            'url': str(row['url'])
                        }
                    }
                    
                    file_issues.append(issue)
                    
                except Exception as e:
                    logger.error(
                        f"Error processing row {idx + 1} in {csv_file.name}: {str(e)}"
                    )
                    file_errors += 1
            
            logger.info(
                f"Loaded {len(file_issues)} issues from {csv_file.name} "
                f"({file_errors} errors)"
            )
            
            all_issues.extend(file_issues)
            total_errors += file_errors
            
        except Exception as e:
            logger.error(f"Failed to process file {csv_file.name}: {str(e)}")
            continue
    
    logger.info(
        f"CSV loading complete: {len(all_issues)} issues loaded from "
        f"{len(csv_files)} file(s) with {total_errors} total errors"
    )
    
    return all_issues
