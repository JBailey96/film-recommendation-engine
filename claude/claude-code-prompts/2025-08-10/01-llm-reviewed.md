
# CONTEXT

- The application is for data analysis on your IMDb ratings and to have a natural language conversation about it.
- The goal is eventually (not now) to have recommendations.
- The backend is Python, the frontend is React, and there is a Docker-based deployment with Postgres, MCP server, and the app.
- You have access to the IMDb ratings MCP server to query data.
- IMDb rating data from `imdb_rating.csv` is already loaded in and can be queried.
- You have access to Playwright for scraping if needed.
- The import-csv process must be on the website.
- Do not include the Claude API key in any API endpoints.
- Use modern libraries and good practices, but do not over-refactor unless highly beneficial for the listed points.
- This applies to both the React frontend and Python backend, and all dependencies in between.

# TASKS

1. Implement chat history management: allow saving, clearing, and choosing chats. Add a save (floppy disk) icon to save an interaction, moving it into a dropdown list at the top left of the chat window. Allow choosing and resuming chats. Limit to 10 interactions, and note this in the UI.
2. Evaluate if the current flow is agentic. Assess the use of multiple function calls and how LLM agentic flow libraries (e.g., llama-type flow) could improve the process. Produce a document summarizing options and recommendations.
3. Change the timestamp color on chat responses to black for both user and response, as the response has a white background.
4. Add movie posters to the movies layout. Research the best poster source and implement it. If no public source, use the IMDb URL in `imdb_rating.csv` to enrich the DB with image links. Use Playwright to check and, if needed, set up a Playwright Docker container for scraping.
5. Create a script called `psql` in the project root to connect to the database via CLI and run commands. Use it to analyze data as well. Add a rule file in the project root with a short guide on how to use this script.
6. Fix import data functionality: it should be incremental and upload CSV. Remove all references to scraping IMDb URLs and specifying Claude API key.
7. Update Docker to log where each component (Postgres, MCP server, app) is hosted.
8. Use a Postgres socket in Docker config instead of specific ports and passwords; avoid custom configuration.
9. Update the README for both MCP and Docker.
10. Ensure the Claude API key is not present in any API endpoints. The IMDb scraping flow should go through the UI and work as intended. The import-CSV process must be on the website.
11. Test all changes by running Docker, using Playwright MCP, visiting http://localhost:8000/, and verifying data presentation.
12. Use modern libraries and good practices, but avoid excessive refactoring unless highly beneficial for the above points.
13. (Reminder) You have access to the IMDb ratings MCP server for data queries.
14. (Reminder) IMDb rating data from `imdb_rating.csv` is already loaded and can be queried.
15. Produce a document listing 5 specific improvements for the application and a plan for future recommendation features. Place this document in the project root.