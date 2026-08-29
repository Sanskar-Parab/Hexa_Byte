"""Deterministic skill-name normalization and alias resolution.

External sources (job/internship postings) and our own skill catalog frequently name the
same underlying skill differently — "React" vs "React.js" vs "React JS". This
module resolves those variants without calling the LLM, which is reserved for
genuinely ambiguous/contextual cases (see app.ai.groq_client).
"""
import re

# Maps a normalized raw phrase -> canonical skill key. Both sides are
# lowercase/whitespace-normalized before lookup (see normalize_skill_name).
ALIASES: dict[str, str] = {
    "javascript": "javascript",
    "js": "javascript",
    "java script": "javascript",
    "javascript development": "javascript",
    "ecmascript": "javascript",
    "es6": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "react native": "react native",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "node js": "node.js",
    "express": "express.js",
    "expressjs": "express.js",
    "express.js": "express.js",
    "express js": "express.js",
    "vue": "vue.js",
    "vuejs": "vue.js",
    "vue.js": "vue.js",
    "vue js": "vue.js",
    "angular": "angular",
    "angularjs": "angular",
    "angular js": "angular",
    "next": "next.js",
    "nextjs": "next.js",
    "next.js": "next.js",
    "next js": "next.js",
    "html": "html/css",
    "css": "html/css",
    "html5": "html/css",
    "css3": "html/css",
    "html/css": "html/css",
    "html & css": "html/css",
    "git": "git",
    "github": "git",
    "git/github": "git",
    "gitlab": "git",
    "version control": "git",
    "python": "python",
    "python3": "python",
    "python programming": "python",
    "sql": "sql",
    "mysql": "sql",
    "postgresql": "sql",
    "postgres": "sql",
    "database management": "sql",
    "c++": "c++",
    "cpp": "c++",
    "c#": "c#",
    "csharp": "c#",
    "dot net": ".net",
    ".net": ".net",
    "java": "java",
    "aws": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "machine learning": "machine learning",
    "ml": "machine learning",
    "deep learning": "deep learning",
    "artificial intelligence": "artificial intelligence",
    "ai": "artificial intelligence",
    "data analysis": "data analysis",
    "data analytics": "data analysis",
    "data science": "data science",
    "figma": "figma",
    "adobe xd": "figma",
    "ui/ux": "ui/ux design",
    "ux": "ui/ux design",
    "ui": "ui/ux design",
    "ui design": "ui/ux design",
    "ux design": "ui/ux design",
    "user interface design": "ui/ux design",
    "user experience design": "ui/ux design",
    "communication": "communication",
    "communication skills": "communication",
    "problem solving": "problem solving",
    "problem-solving": "problem solving",
    "team management": "team management",
    "leadership": "leadership",
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "rest api": "rest api",
    "restful api": "rest api",
    "api development": "rest api",
    "api": "rest api",
    "graphql": "graphql",
    "web development": "web development",
    "web developer": "web development",
    "web dev": "web development",
    "frontend development": "frontend development",
    "front-end development": "frontend development",
    "front end development": "frontend development",
    "frontend": "frontend development",
    "backend development": "backend development",
    "back-end development": "backend development",
    "back end development": "backend development",
    "backend": "backend development",
    "full stack development": "full stack development",
    "fullstack development": "full stack development",
    "full-stack development": "full stack development",
    "full stack": "full stack development",
    "data structures": "data structures & algorithms",
    "data structures and algorithms": "data structures & algorithms",
    "dsa": "data structures & algorithms",
    "algorithms": "data structures & algorithms",
    "excel": "excel",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "power bi": "power bi",
    "tableau": "tableau",
    "content writing": "content writing",
    "digital marketing": "digital marketing",
    "seo": "seo",
    "linux": "linux",
    "bash": "shell scripting",
    "shell scripting": "shell scripting",
}

_QUALIFIER_PATTERN = re.compile(
    r"\b(development|developer|programming|framework|language|skills?)\b"
)
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_skill_name(name: str) -> str:
    """Reduce a raw skill string to a canonical lowercase key using known aliases.

    Falls back to a cleaned lowercase version of the input when no alias is
    known, so unfamiliar skills still get consistent, comparable keys.
    """
    if not name:
        return ""
    cleaned = _WHITESPACE_PATTERN.sub(" ", name.strip().lower()).strip(" .")
    if cleaned in ALIASES:
        return ALIASES[cleaned]

    stripped = _QUALIFIER_PATTERN.sub("", cleaned).strip()
    stripped = _WHITESPACE_PATTERN.sub(" ", stripped).strip(" .")
    if stripped and stripped in ALIASES:
        return ALIASES[stripped]

    return stripped or cleaned


def build_alias_index(known_names: list[str]) -> dict[str, str]:
    """Map normalized keys -> the canonical display name from `known_names`.

    `known_names` is typically the set of skill names the user already has in
    their profile (from the `skills` table), preserving the DB's display casing.
    """
    index: dict[str, str] = {}
    for name in known_names:
        key = normalize_skill_name(name)
        if key:
            index.setdefault(key, name)
    return index


def match_skill_to_known(raw_skill: str, known_index: dict[str, str]) -> str | None:
    """Resolve a raw skill string (e.g. from a job/internship posting) to a known display name.

    Tries exact normalized match first, then a conservative substring match
    (e.g. "React Native" contains "react" so it won't falsely match "react",
    but "Node" and "Node.js" normalize to the same key already via aliases).
    """
    key = normalize_skill_name(raw_skill)
    if not key:
        return None
    if key in known_index:
        return known_index[key]

    for norm_key, display_name in known_index.items():
        if not norm_key or len(norm_key) <= 2 or len(key) <= 2:
            continue
        if key == norm_key:
            return display_name
        if key.startswith(norm_key + " ") or norm_key.startswith(key + " "):
            return display_name

    return None


def dedupe_skill_names(skill_names: list[str]) -> list[str]:
    """Collapse duplicate/near-duplicate skill strings (e.g. "JavaScript" listed twice)."""
    seen = set()
    result = []
    for name in skill_names:
        if not isinstance(name, str):
            continue
        key = normalize_skill_name(name)
        if key and key not in seen:
            seen.add(key)
            result.append(name.strip())
    return result
