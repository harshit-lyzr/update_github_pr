import os

from fastapi import FastAPI, HTTPException
import requests
from pydantic import BaseModel
import re
from dotenv import load_dotenv

# Initialize FastAPI app
app = FastAPI()

load_dotenv()
# Replace with your GitHub token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Headers for authentication
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


# PR description update model
class PRUpdateRequest(BaseModel):
    description: str


# Helper function to extract repo owner, repo name, and PR number from URL
def parse_github_pr_url(url: str):
    pattern = r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<pr_number>\d+)"
    match = re.search(pattern, url)
    if match:
        return match.group("owner"), match.group("repo"), match.group("pr_number")
    else:
        raise ValueError("Invalid GitHub Pull Request URL format")


@app.get("/pr/files")
def get_pr_files(pr_url: str):
    """Fetch files changed in a pull request based on full PR URL"""
    try:
        owner, repo, pr_number = parse_github_pr_url(pr_url)
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            files_data = response.json()

            # Format the response to show relevant file details
            formatted_files = []
            for file in files_data:
                formatted_files.append({
                    "filename": file['filename'],
                    "changes": file['changes'],
                    "patch": file.get('patch', 'No patch available')  # Patch may be missing in some cases
                })

            return {"files": formatted_files}
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch PR files")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/pr")
def update_pr_description(pr_url: str, pr_update: PRUpdateRequest):
    """Update pull request description based on full PR URL"""
    try:
        owner, repo, pr_number = parse_github_pr_url(pr_url)
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        # Data to be sent in the PATCH request (updating PR body)
        data = {
            'body': pr_update.description
        }

        response = requests.patch(url, headers=headers, json=data)
        print(response.content)
        if response.status_code == 200:
            return {"message": f"Successfully updated PR #{pr_number} description."}
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to update PR description")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# To run this FastAPI app:
# Save this as a Python file (e.g., main.py), then run: `uvicorn main:app --reload`
