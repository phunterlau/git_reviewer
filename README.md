# GitHub Commit Reviewer

A Python tool that fetches commits from a GitHub repository for a specific user and uses GPT-4o to analyze the programmer's capabilities and coding patterns.

## Setup

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   uv pip install PyGithub openai python-dotenv
   ```

4. **Configure API keys**:
   - Copy the `.env` file and add your API keys:
     - `GITHUB_TOKEN`: Generate at https://github.com/settings/tokens (needs `repo` scope)
     - `OPENAI_API_KEY`: Get from https://platform.openai.com/api-keys

## Usage

Run the tool using uv (recommended):
```bash
uv run python main.py
```

This automatically manages dependencies via the `pyproject.toml` configuration.

Or if you prefer to use the virtual environment:
```bash
source .venv/bin/activate
python main.py
```

You will be prompted to enter:
1. **GitHub email or username**: The email address or GitHub username of the user to analyze
2. **GitHub repository URL**: The repository to search (e.g., `https://github.com/owner/repo` or just `owner/repo`)
3. **Analysis type**: Choose what to analyze:
   - Commits only
   - Issues only  
   - Pull requests only
   - All (commits, issues, and pull requests)

## Output

The tool generates files based on what data is found:

1. **commits_[identifier].md**: Markdown file containing all commits by the specified user
2. **commits_[identifier]_review.json**: JSON file with GPT-4o's analysis (for commits)
3. **issues_[identifier].md**: Markdown file containing all issues created by the user
4. **pull_requests_[identifier].md**: Markdown file containing all pull requests created by the user

The GPT-4o analysis includes:
   - Programming language expertise
   - Commit quality assessment
   - Coding style analysis
   - Technical skills demonstrated
   - Overall rating and recommendations

## Example

```bash
$ python main.py
GitHub login email: developer@example.com
GitHub repository URL: https://github.com/owner/awesome-project

# Tool will fetch commits and generate review...
```

## File Structure

```
.
├── .venv/              # Virtual environment
├── .env                # API keys (not in git)
├── main.py             # Main script
├── github_utils.py     # GitHub API functions
├── gpt_utils.py        # OpenAI GPT functions
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## Requirements

- Python 3.7+
- GitHub Personal Access Token
- OpenAI API Key
- Internet connection
