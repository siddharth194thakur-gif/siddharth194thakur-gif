#!/usr/bin/env python3
"""
update_showcase.py — Automatic GitHub Project Showcase Generator
Fetches public repositories, detects technologies, descriptions, and live demos,
and automatically updates the README.md showcase section between comment markers.
Zero external dependencies (uses standard Python 3 libraries only).
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

START_MARKER = "<!-- AUTO-GENERATED-PROJECTS:START -->"
END_MARKER = "<!-- AUTO-GENERATED-PROJECTS:END -->"

# Known technology topic mappings for clean capitalization
TOPIC_TECH_MAP = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "django": "Django",
    "django-rest-framework": "Django REST Framework",
    "drf": "Django REST Framework",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "react": "React",
    "reactjs": "React",
    "nextjs": "Next.js",
    "next": "Next.js",
    "vue": "Vue",
    "vuejs": "Vue",
    "nodejs": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "tailwindcss": "Tailwind CSS",
    "tailwind": "Tailwind CSS",
    "html5": "HTML5",
    "html": "HTML5",
    "css3": "CSS3",
    "css": "CSS3",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "docker": "Docker",
    "vite": "Vite",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "jwt": "JWT Auth",
    "jwt-authentication": "JWT Auth",
    "glassmorphism": "Glassmorphism UI",
    "calculator": "Calculator",
    "cli-tool": "CLI Tool",
}

DEPENDENCY_TECH_MAP = {
    "django": "Django",
    "djangorestframework": "Django REST Framework",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "tailwindcss": "Tailwind CSS",
    "vite": "Vite",
    "express": "Express.js",
    "mongoose": "MongoDB",
    "pg": "PostgreSQL",
    "psycopg2": "PostgreSQL",
    "psycopg": "PostgreSQL",
}


def get_token() -> Optional[str]:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def github_request(url: str) -> Optional[Any]:
    """Execute a GitHub API GET request with error handling and rate limit detection."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Siddharth-Showcase-Automation")
    req.add_header("Accept", "application/vnd.github.v3+json")

    token = get_token()
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code == 403:
            print(f"[Warning] GitHub API 403 (Rate limit or forbidden) for {url}: {e.reason}", file=sys.stderr)
            return None
        print(f"[Warning] HTTP {e.code} for {url}: {e.reason}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"[Warning] Network error for {url}: {exc}", file=sys.stderr)
        return None


def fetch_readme_text(owner: str, repo: str) -> Optional[str]:
    """Fetch and decode the default branch README of a repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    data = github_request(url)
    if not data or "content" not in data:
        return None
    try:
        import base64
        raw = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return raw
    except Exception:
        return None


def detect_live_url_from_readme(readme_text: str) -> Optional[str]:
    """Extract an explicit deployment / live demo URL from README text."""
    if not readme_text:
        return None

    # 1. Search for markdown links labeled with live/demo/website
    label_pattern = re.compile(
        r'\[(?:🚀\s*|🌐\s*)?(?:Live\s*Demo|Live\s*Site|Live\s*Platform|Website|Demo|Deployment)\]\((https?://[^\s\)]+)\)',
        re.IGNORECASE
    )
    match = label_pattern.search(readme_text)
    if match:
        url = match.group(1).strip()
        if not url.startswith("https://github.com"):
            return url

    # 2. Search for common production hosting domains
    domain_pattern = re.compile(
        r'https?://[a-zA-Z0-9_\-\.]+\.(?:vercel\.app|onrender\.com|netlify\.app|github\.io)(?:/[^\s\)\"\']*)?'
    )
    match = domain_pattern.search(readme_text)
    if match:
        return match.group(0).strip()

    return None


def extract_description_from_readme(readme_text: str) -> Optional[str]:
    """Extract the first meaningful descriptive paragraph from a README."""
    if not readme_text:
        return None

    lines = readme_text.splitlines()
    candidate_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Skip headers, badges, images, horizontal rules, blank lines
        if not stripped:
            if candidate_lines:
                break
            continue
        if stripped.startswith(("#", "<", "!", "[!", "---", "===", "```")):
            continue
        # Skip badge links
        if re.match(r'^\[!\[.*\]\(.*\)\]\(.*\)$', stripped) or re.match(r'^!\[.*\]\(.*\)$', stripped):
            continue
        candidate_lines.append(stripped)

    if candidate_lines:
        full_desc = " ".join(candidate_lines)
        # Clean markdown links or formatting
        cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', full_desc)
        cleaned = re.sub(r'[*_`]', '', cleaned)
        if len(cleaned) > 200:
            cleaned = cleaned[:197].rsplit(" ", 1)[0] + "..."
        if len(cleaned) > 20:
            return cleaned

    return None


def detect_technologies(owner: str, repo: str, repo_data: Dict[str, Any], readme_text: Optional[str]) -> List[str]:
    """Detect technologies from languages, topics, and root project files."""
    detected: List[str] = []
    seen: Set[str] = set()

    def add_tech(name: str):
        key = name.lower()
        if key not in seen:
            seen.add(key)
            detected.append(name)

    # 1. Primary languages from GitHub API
    lang_data = github_request(f"https://api.github.com/repos/{owner}/{repo}/languages") or {}
    for lang in lang_data.keys():
        if lang not in ["Shell", "Makefile", "Dockerfile"]:
            add_tech(lang)

    # 2. Repository Topics
    topics = repo_data.get("topics", [])
    for topic in topics:
        topic_lower = topic.lower()
        if topic_lower in TOPIC_TECH_MAP:
            add_tech(TOPIC_TECH_MAP[topic_lower])

    # 3. Check repository contents (requirements.txt, package.json, manage.py, Dockerfile)
    contents = github_request(f"https://api.github.com/repos/{owner}/{repo}/contents") or []
    file_names = {item.get("name", "").lower(): item for item in contents if isinstance(item, dict)}

    if "manage.py" in file_names:
        add_tech("Django")

    if "dockerfile" in file_names or "docker-compose.yml" in file_names:
        add_tech("Docker")

    if "requirements.txt" in file_names and "content" in file_names["requirements.txt"]:
        try:
            import base64
            req_text = base64.b64decode(file_names["requirements.txt"]["content"]).decode("utf-8", errors="ignore").lower()
            for pkg, name in DEPENDENCY_TECH_MAP.items():
                if pkg in req_text:
                    add_tech(name)
        except Exception:
            pass

    if "package.json" in file_names and "content" in file_names["package.json"]:
        try:
            import base64
            pkg_json = json.loads(base64.b64decode(file_names["package.json"]["content"]).decode("utf-8", errors="ignore"))
            all_deps = {**pkg_json.get("dependencies", {}), **pkg_json.get("devDependencies", {})}
            for dep in all_deps.keys():
                dep_lower = dep.lower()
                for key, name in DEPENDENCY_TECH_MAP.items():
                    if key in dep_lower:
                        add_tech(name)
        except Exception:
            pass

    # 4. Fallback search inside README text
    if readme_text:
        readme_lower = readme_text.lower()
        if "postgresql" in readme_lower:
            add_tech("PostgreSQL")
        if "fastapi" in readme_lower:
            add_tech("FastAPI")
        if "tailwind" in readme_lower:
            add_tech("Tailwind CSS")

    # Limit to top 6 most relevant tech tags
    return detected[:6]


def format_project_card(project: Dict[str, Any]) -> str:
    """Format a single repository into a clean, modern GitHub markdown card."""
    title = project["title"]
    repo_url = project["url"]
    description = project.get("description", "").strip()
    tech_stack = project.get("tech_stack", [])
    stars = project.get("stars", 0)
    forks = project.get("forks", 0)
    live_demo = project.get("live_demo")
    updated = project.get("updated", "")

    # Clean description
    desc_line = f"> {description}" if description else "> *Practical software project built with modern developer workflows.*"

    # Tech stack line
    if tech_stack:
        tech_badges = " • ".join(f"`{t}`" for t in tech_stack)
        tech_line = f"- 🛠️ **Tech Stack**: {tech_badges}"
    else:
        tech_line = ""

    # Stats and date
    stat_parts = []
    if stars > 0:
        stat_parts.append(f"⭐ **{stars}**")
    if forks > 0:
        stat_parts.append(f"🍴 **{forks}**")
    if updated:
        stat_parts.append(f"🕒 *Updated {updated}*")
    stat_line = f"- 📌 **Activity**: {' • '.join(stat_parts)}" if stat_parts else ""

    # Links
    links = [f"[GitHub Repository]({repo_url})"]
    if live_demo:
        links.append(f"[🌐 Live Demo]({live_demo})")
    link_line = f"- 🔗 **Links**: {' &bull; '.join(links)}"

    # Assemble card
    card_lines = [
        f"#### 🚀 [{title}]({repo_url})",
        desc_line,
    ]
    if tech_line:
        card_lines.append(tech_line)
    if stat_line:
        card_lines.append(stat_line)
    card_lines.append(link_line)

    return "\n".join(card_lines)


def main():
    root_dir = Path(__file__).resolve().parent.parent
    config_path = root_dir / "showcase_config.json"
    readme_path = root_dir / "README.md"

    if not config_path.exists():
        print(f"[Error] Configuration file not found at {config_path}", file=sys.stderr)
        sys.exit(1)

    if not readme_path.exists():
        print(f"[Error] README.md not found at {readme_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    username = config.get("username", "siddharth194thakur-gif")
    max_projects = config.get("max_projects", 8)
    featured_repos = [r.lower() for r in config.get("featured_repositories", [])]
    excluded_repos = set(r.lower() for r in config.get("excluded_repositories", []))
    excluded_topics = set(t.lower() for t in config.get("excluded_topics", []))
    include_forks = config.get("include_forks", False)
    custom_overrides = config.get("custom_overrides", {})

    print(f"Fetching public repositories for @{username}...")
    api_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=public&sort=updated"
    repos = github_request(api_url)

    if not repos or not isinstance(repos, list):
        print(f"[Warning] No repositories found or GitHub API unavailable. Keeping existing showcase intact.")
        sys.exit(0)

    # Filter eligible repositories
    eligible_repos = []
    for r in repos:
        name = r.get("name", "")
        name_lower = name.lower()

        if name_lower in excluded_repos:
            continue
        if r.get("fork", False) and not include_forks:
            continue
        if r.get("private", False):
            continue

        topics = set(t.lower() for t in r.get("topics", []))
        if topics.intersection(excluded_topics):
            continue

        eligible_repos.append(r)

    # Sorting: Featured first (in exact order specified), then remaining by updated_at
    def get_sort_key(r):
        name_lower = r.get("name", "").lower()
        if name_lower in featured_repos:
            return (0, featured_repos.index(name_lower))
        # Non-featured sorted by updated_at descending
        updated_at = r.get("updated_at", "")
        return (1, -datetime.fromisoformat(updated_at.replace("Z", "+00:00")).timestamp() if updated_at else 0)

    eligible_repos.sort(key=get_sort_key)
    selected_repos = eligible_repos[:max_projects]

    print(f"Processing {len(selected_repos)} selected projects...")
    projects_data = []

    for r in selected_repos:
        name = r.get("name", "")
        overrides = custom_overrides.get(name, {})
        readme_text = fetch_readme_text(username, name)

        # 1. Title
        title = overrides.get("title") or name.replace("-", " ").replace("_", " ").title()

        # 2. Description
        desc = (
            overrides.get("description")
            or r.get("description")
            or extract_description_from_readme(readme_text)
            or ""
        ).strip()

        # 3. Live Demo
        homepage = r.get("homepage", "").strip() if r.get("homepage") else ""
        if homepage and ("github.com" in homepage or homepage == r.get("html_url")):
            homepage = ""
        live_demo = (
            overrides.get("live_demo")
            or (homepage if homepage.startswith("http") else None)
            or detect_live_url_from_readme(readme_text)
        )

        # 4. Tech stack
        tech = detect_technologies(username, name, r, readme_text)

        # 5. Date formatting
        updated_raw = r.get("updated_at", "")
        updated_fmt = ""
        if updated_raw:
            try:
                dt = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
                updated_fmt = dt.strftime("%b %Y")
            except Exception:
                pass

        projects_data.append({
            "name": name,
            "title": title,
            "url": r.get("html_url", f"https://github.com/{username}/{name}"),
            "description": desc,
            "tech_stack": tech,
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "live_demo": live_demo,
            "updated": updated_fmt,
        })

    # Generate Markdown Output
    card_blocks = [format_project_card(p) for p in projects_data]
    generated_content = (
        f"{START_MARKER}\n\n"
        + "\n\n---\n\n".join(card_blocks)
        + f"\n\n{END_MARKER}"
    )

    # Read current README.md
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_text = f.read()

    # Verify or insert markers if not present
    if START_MARKER not in readme_text or END_MARKER not in readme_text:
        print("[Info] Markers not found in README.md. Inserting markers under '### 🚀 Projects' section...")
        pattern = re.compile(r'(###\s*🚀\s*Projects\s*\n\s*(?:.*?\n)?)(?:####\s*.*)?(?=\n---\n|\Z)', re.DOTALL)
        if pattern.search(readme_text):
            readme_text = pattern.sub(r'\1\n' + START_MARKER + '\n' + END_MARKER + '\n', readme_text, count=1)
        else:
            readme_text += f"\n\n### 🚀 Projects\n\n{START_MARKER}\n{END_MARKER}\n"

    # Replace content between markers
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL
    )

    current_match = pattern.search(readme_text)
    if current_match and current_match.group(0).strip() == generated_content.strip():
        print("[OK] Showcase is already up to date. No changes needed.")
        return

    updated_readme = pattern.sub(generated_content, readme_text)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_readme)

    print(f"[Success] Updated README.md showcase with {len(projects_data)} projects:")
    for p in projects_data:
        demo_flag = " (🌐 Live)" if p.get("live_demo") else ""
        print(f"  • {p['title']}{demo_flag} — {p['url']}")


if __name__ == "__main__":
    main()
