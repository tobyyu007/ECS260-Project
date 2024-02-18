# Token 1 from GitHub
TOKEN = ""

# Token 2 from GitHub
TOKEN1 = ""

# Token 3 from GitHub
TOKEN2 = ""

# Token 4 from GitHub
TOKEN4 = ""

# Token 5 from GitHub
TOKEN5 = ""

# Token 6 from GitHub
TOKEN6 = ""


# Token 1 from SonarQube
TOKEN3 = ""

REPOSCHARACTERISTICS = [
    "index",
    "repo_name",
    "ncloc",
    "code_smells",
    "any-type_count",
    "cognitive_complexity",
    "framework",
    "bug_issues_count",
    "bug-fix_commits_count",
    "commits_count",
]

METRICS = [
    "index",
    "repo_name",
    "code-smells_ncloc",
    "bug-fix-commits_ratio",
    "avg_bug-issue_time",
    "cognitive-complexity_ncloc",
]

CALCULATEDVALS = ["", "react", "angular", "vue", "others"]

ESLINTFILES = ["./eslint/.eslintignore", "./eslint/.eslintrc.js"]

URLCREATEPROJECT = "http://localhost:9000/api/projects/create"
URLGENERATETOKEN = "http://localhost:9000/api/user_tokens/generate"
URLISSUES = "http://localhost:9000/api/issues/search"
URLCOMPONENTREE = "http://localhost:9000/api/measures/component_tree"

ESLINTPATHS = [
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.js",
    ".eslintignore",
    ".eslintrc.yml",
    ".eslintrc.yaml",
]
