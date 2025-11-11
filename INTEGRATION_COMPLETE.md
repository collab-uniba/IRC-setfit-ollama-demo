# Vector Store UI Integration - Complete

## Summary

The vector store service has been successfully integrated into the UI service, providing users with semantic search capabilities directly in the web interface.

## What Was Added

### 1. New UI Section: "Find Similar Issues"
A collapsible accordion section placed after "Label Management" that includes:

#### A. Vector Store Status Display
- Connection status (Online/Offline/Timeout)
- Number of indexed issues
- Collection name
- Active embedding model
- Manual refresh button

#### B. Similar Issues Search
- Multi-line text input for queries
- Slider to select 1-20 results
- Checkbox to enable/disable reranking
- Results display showing:
  - Issue titles (bold)
  - Similarity scores (0-1 scale)
  - Associated labels
  - Issue state (open/closed)
  - GitHub URLs
  - Body previews (first 200 chars)

#### C. Label Suggestions
- Multi-line text input for issue description
- Slider to consider 3-15 similar issues
- Ranked label suggestions with frequency counts
- Shows how many similar issues have each label

### 2. Backend Functions (services/ui/app.py)

#### search_similar_issues(query_text, top_k, use_rerank)
- Validates vector store availability
- Checks for indexed issues
- Performs semantic search
- Formats results with scores, labels, and previews
- Handles timeouts and connection errors

#### get_vector_store_status()
- Checks service health endpoint
- Returns formatted status with stats
- Handles offline scenarios gracefully

#### suggest_labels_from_similar(query_text, top_k)
- Searches for similar issues
- Aggregates labels from results
- Ranks by frequency
- Returns top 10 label suggestions

### 3. Event Handlers
- Refresh status button
- Search similar issues button
- Get label suggestions button
- Auto-load status on page load

### 4. Error Handling
All functions handle:
- Service offline/unreachable
- Connection timeouts
- Empty collections
- Empty queries
- Network errors

## User Workflows

### Finding Similar Issues
1. User opens "Find Similar Issues" accordion
2. Sees status: "✅ Vector Store: Online, 1234 issues"
3. Enters query: "Memory leak when training"
4. Sets results to 5, enables reranking
5. Clicks "Search Similar Issues"
6. Views results with scores and labels

### Getting Label Suggestions
1. User enters new issue text
2. Sets to consider top 10 similar issues
3. Clicks "Get Label Suggestions"
4. Sees: "bug (6), memory (4), performance (2)"
5. Uses suggestions to label new issue

### Monitoring Service
1. Admin opens accordion
2. Checks status display
3. Clicks refresh if needed
4. Verifies issue count

## Benefits

1. **Duplicate Detection** - Find similar issues before creating new ones
2. **Label Discovery** - Data-driven label suggestions from historical issues
3. **Better Classification** - Complement SetFit/Ollama with similar issue analysis
4. **Workflow Efficiency** - Faster issue triaging with semantic search
5. **Data Quality** - Reduce duplicates and improve label consistency

## Technical Details

### Dependencies
No new dependencies required - uses existing `requests` library

### Environment Variables
Uses `VECTOR_STORE_BASE_URL` from environment (configured in docker-compose)

### API Integration
Calls vector store endpoints:
- GET `/health` - Service status
- POST `/search` - Semantic search with optional reranking

### Timeout Settings
- Health check: 5 seconds
- Search queries: 30 seconds

### Response Format
All functions return formatted strings for Gradio display with:
- Markdown formatting for emphasis
- Clear section separators
- Structured output for readability

## Files Modified

- `services/ui/app.py` - Added 180+ lines of code
  - 3 new functions
  - 1 new environment variable
  - UI components for accordion section
  - Event handlers

## Testing

The integration includes:
- Input validation (empty queries)
- Service availability checks
- Error handling for all failure modes
- Graceful degradation when service offline

## Documentation

Created:
- `UI_INTEGRATION_SUMMARY.md` - High-level overview
- `UI_FEATURES.md` - Detailed features and workflows
- `UI_MOCKUP.txt` - ASCII mockup of UI layout

## Next Steps for Users

1. Start services with `docker compose up`
2. Wait for vector store to load CSV data (~1-2 minutes)
3. Open UI at http://localhost:7860
4. Navigate to "Find Similar Issues" accordion
5. Check status shows "Online" with issue count
6. Try searching for similar issues
7. Get label suggestions for new issues

## Maintenance

To update indexed issues:
1. Add/update CSV files in `data/` directory
2. Call `/reindex` endpoint or restart service
3. UI will automatically show updated count

## Support

If status shows offline:
- Verify vector store service is running
- Check docker compose logs
- Ensure port 8001 is accessible
- Verify CSV data loaded successfully

## Conclusion

The vector store service is now fully integrated into the UI, providing users with powerful semantic search capabilities to find similar issues, discover relevant labels, and improve issue management workflows.
