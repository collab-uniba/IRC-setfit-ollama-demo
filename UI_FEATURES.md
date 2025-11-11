# Vector Store UI Integration - Features Added

## New "Find Similar Issues" Section

This collapsible accordion section provides three main capabilities:

### 1. Vector Store Status Monitor
- Shows real-time connection status
- Displays number of indexed issues
- Shows which embedding model is active
- Refresh button to update status on demand

### 2. Similar Issues Search
**Input Fields:**
- Multi-line text box for query
- Slider to select 1-20 results
- Checkbox to enable/disable reranking

**Output Display:**
For each similar issue found:
- Issue title (bold)
- Similarity score (0-1 scale)
- Associated labels
- Issue state (open/closed)
- GitHub URL
- Preview of issue body (first 200 chars)

### 3. Label Suggestions
**Input Fields:**
- Multi-line text box for issue description
- Slider to consider 3-15 similar issues

**Output Display:**
- List of suggested labels
- Frequency count for each label
- Based on labels from similar issues

## User Workflow Examples

### Example 1: Finding Duplicates
1. User writes a new issue: "Application crashes when loading large datasets"
2. Opens "Find Similar Issues" section
3. Pastes issue text into search box
4. Clicks "Search Similar Issues"
5. Sees 5 similar issues including:
   - "Crash when loading large datasets" (score: 0.91)
   - "App crashes with big data files" (score: 0.85)
6. Identifies issue #128 as a duplicate
7. Can reference it instead of creating new issue

### Example 2: Getting Label Suggestions
1. User has new issue text about memory problems
2. Goes to "Get Label Suggestions" section
3. Pastes issue text
4. Sets slider to consider top 10 similar issues
5. Clicks "Get Label Suggestions"
6. Gets suggestions: bug (6), memory (4), performance (2)
7. Applies these labels to new issue

### Example 3: Monitoring Vector Store
1. Admin wants to check if vector store is working
2. Opens "Find Similar Issues" section
3. Sees status: "✅ Vector Store: Online, 1234 issues"
4. Or sees: "❌ Vector Store: Offline" if down
5. Can click refresh to update status

## Error Handling

The UI gracefully handles various scenarios:

- **Service Offline**: Shows clear offline message with connection details
- **No Issues Indexed**: Prompts user to index issues first
- **Query Timeout**: Explains that query might be too complex
- **Connection Error**: Shows friendly error with service URL
- **Empty Query**: Prompts user to enter text

## Integration Benefits

1. **Duplicate Detection**: Find similar issues before creating new ones
2. **Label Discovery**: Get data-driven label suggestions
3. **Historical Context**: Learn from past issues
4. **Workflow Efficiency**: Faster issue triaging
5. **Data Quality**: Reduce duplicate issues in repository
