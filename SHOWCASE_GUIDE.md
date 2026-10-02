# 🚀 Automatic GitHub Project Showcase System — User Guide

Welcome to your automated GitHub Project Showcase system! With this setup, you **never** need to ask an AI or manually edit your `README.md` whenever you create or update a GitHub repository.

---

## 📌 1. What Was Created

| File | Purpose |
|---|---|
| `scripts/update_showcase.py` | Standalone Python automation engine that queries GitHub API, detects tech stacks, parses descriptions, identifies live demos, and updates `README.md` between comment markers. Zero external dependencies. |
| `showcase_config.json` | Easy configuration file where you control featured projects, excluded repos, topics, and custom overrides without touching code. |
| `.github/workflows/update-showcase.yml` | Native GitHub Action that runs every 6 hours, on config push, or via manual click. Commits only when changes actually occur. |
| `README.md` | Your profile README updated with dynamic `<!-- AUTO-GENERATED-PROJECTS:START -->` and `<!-- AUTO-GENERATED-PROJECTS:END -->` markers. All your existing headers, badges, and stats remain 100% untouched. |

---

## ⚙️ 2. How the Automation Works

```
Create or Update a GitHub Repository
               ↓
GitHub Actions triggers automatically (every 6 hours or via manual button)
               ↓
scripts/update_showcase.py fetches your public repositories via GitHub API
               ↓
Filters out excluded repos & topics (e.g. profile repo, practice tests)
               ↓
Detects tech stack (files, dependencies, topics, languages) & live demo URLs
               ↓
Formats beautiful project cards
               ↓
Injects cards into README.md between the AUTO-GENERATED markers
               ↓
If changes detected → commits & pushes with [skip ci]
If no changes → skips commit (no unnecessary commits!)
```

---

## 🔄 3. How to Use It in the Future (Your Daily Workflow)

Whenever you build a new project:

1. **Create your repository on GitHub** (e.g., `ML-Predictor` or `AI-Agent`).
2. **Push your code to it.**
   - *Tip*: Add a short 1-line description in repository settings and 2-3 GitHub topics (e.g., `python`, `fastapi`, `machine-learning`).
   - *Tip*: If you deployed on Vercel/Render/Netlify, put the URL in the repo's **Website / Homepage** field.
3. **Done!**
   - The workflow will automatically pick it up during its regular run (or you can click "Run workflow" in GitHub Actions for instant sync).
   - Your profile README will update itself automatically!

---

## 🛠️ 4. How to Customize (`showcase_config.json`)

All configuration is in `showcase_config.json` in the root of your profile repository:

### A. How to Pin/Feature a Project
Featured projects always appear at the top in the exact order you list them:
```json
"featured_repositories": [
  "My-Best-Project",
  "Hostel-Talkies-Frontend",
  "Calculator"
]
```

### B. How to Exclude a Repository
If you created a test repo or practice assignment that you **don't** want on your profile:
```json
"excluded_repositories": [
  "siddharth194thakur-gif",
  "practice-repo",
  "test-dsa"
]
```
*(Or simply add the GitHub topic `no-showcase` to any repository on GitHub and it will be excluded automatically!)*

### C. How to Change Number of Displayed Projects
Change `"max_projects"`:
```json
"max_projects": 6
```

### D. Optional Custom Overrides (Custom Title or Live Link)
If you want to customize how a project title or description appears:
```json
"custom_overrides": {
  "My-Repo-Name": {
    "title": "Super Cool Project Name",
    "description": "Custom detailed description here...",
    "live_demo": "https://my-app.vercel.app"
  }
}
```

---

## 🔘 5. How to Manually Trigger the Workflow

You don't have to wait 6 hours if you just pushed a new repo and want your profile updated immediately:

1. Go to your repository on GitHub: `https://github.com/siddharth194thakur-gif/siddharth194thakur-gif`
2. Click on the **Actions** tab at the top.
3. In the left sidebar, click **Auto-Update Project Showcase**.
4. Click the **Run workflow** dropdown button on the right, and click the green **Run workflow** button.
5. In ~15 seconds, the workflow finishes and your profile is updated!

---

## 🔐 6. GitHub Setup & Authentication

- **Zero extra tokens or secrets needed!** The workflow uses the built-in `GITHUB_TOKEN` provided automatically by GitHub Actions.
- In your repository settings:
  - Go to **Settings** → **Actions** → **General**
  - Scroll down to **Workflow permissions**
  - Ensure **"Read and write permissions"** is selected (this allows GitHub Actions to push the updated `README.md`).

---

## 🛡️ 7. Safety & Idempotence

- **Marker Protection**: Only the content between `<!-- AUTO-GENERATED-PROJECTS:START -->` and `<!-- AUTO-GENERATED-PROJECTS:END -->` is touched. Everything else in `README.md` (Hero banner, typing animation, stats, contribution snake, contact links) is completely preserved.
- **Smart Diff**: If no project data has changed, the script exits without committing, preventing messy commit histories.
- **Error Resilience**: If a repository has no README, no description, or invalid metadata, the system falls back gracefully without breaking other projects.
