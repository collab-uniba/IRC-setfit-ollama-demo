# UI Integration Summary

## New Features Added to UI Service

### 1. Vector Store Status Display
Shows real-time status of the vector store service including:
- Connection status (Online/Offline)
- Number of indexed issues
- Collection name
- Embedding model in use

### 2. Similar Issues Search
Users can:
- Enter a query (issue title/description)
- Set number of results to return (1-20)
- Toggle reranking for better accuracy
- View results with:
  - Similarity scores
  - Issue titles and labels
  - Issue state (open/closed)
  - GitHub URLs
  - Body preview (first 200 chars)

### 3. Label Suggestions
Based on similar historical issues:
- Enter issue text
- Specify how many similar issues to consider (3-15)
- Get suggested labels ranked by frequency
- See how many similar issues have each label

## UI Layout

The new "Find Similar Issues" section is added as a collapsible accordion after the Label Management section.

### Section Structure:
```
🔍 Find Similar Issues (Accordion - collapsed by default)
├── Vector Store Status
│   └── Status display with refresh button
│
├── Search by Text
│   ├── Query input (multi-line textbox)
│   ├── Number of Results slider (1-20)
│   ├── Use Reranking checkbox
│   ├── Search button
│   └── Results display area
│
└── Get Label Suggestions
    ├── Issue Text input (multi-line)
    ├── Top N Similar Issues slider (3-15)
    ├── Get Suggestions button
    └── Suggested Labels display area
```

## Example Usage Flow

### Finding Similar Issues:
1. User opens "Find Similar Issues" accordion
2. Status shows: "✅ Vector Store: Online, Indexed Issues: 1234"
3. User enters: "Memory leak when training large models"
4. Sets results to 5, enables reranking
5. Clicks "Search Similar Issues"
6. Results show 5 similar issues with scores, labels, and links

### Getting Label Suggestions:
1. User enters new issue text
2. Sets to consider top 10 similar issues
3. Clicks "Get Label Suggestions"
4. System shows: "bug (3 issues), memory (2 issues), performance (1 issue)"

## Error Handling

The UI handles various error scenarios gracefully:
- **Service Offline**: Shows "❌ Vector Store: Offline" with connection info
- **No Issues Indexed**: Prompts user to index issues first
- **Timeout**: Informs user the query might be too complex
- **Connection Error**: Shows friendly error with service URL

## Integration with Existing Features

The vector store features complement existing functionality:
- Use similar issues to find duplicate issues before creating new ones
- Get label suggestions to improve manual issue classification
- Cross-reference with SetFit and Ollama classification results
- Helps populate the label management system with commonly used labels
