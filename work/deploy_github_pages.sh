#!/usr/bin/env bash
set -e

# Configuration
REPO_NAME="landing-page-demo"
ORG=""  # leave empty to create under your user account; set to "orgname" to create under an organization

# Create temporary working directory
WORKDIR=$(mktemp -d)
cd "$WORKDIR"

# Create repository files
cat > index.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Landing Page</title>
</head>
<body>
  <h1>Welcome to our Landing Page</h1>
  <p>This is a simple index.html file hosted on GitHub Pages.</p>
</body>
</html>
EOF

cat > pricing.md <<'EOF'
# Pricing

| Plan | Price |
|------|-------|
| Free | \$0 |
| Pro  | \$9.99/month |
EOF

cat > README.md <<'EOF'
# Landing Page Demo

This repository contains a simple landing page that is hosted on GitHub Pages.
EOF

# Initialize git repository
git init
git add .
git commit -m "Initial commit"

# Create GitHub repository using gh CLI
if [ -z "$ORG" ]; then
  gh repo create "$REPO_NAME" --public --source=. --remote=origin --push --confirm
else
  gh repo create "$ORG/$REPO_NAME" --public --source=. --remote=origin --push --confirm
fi

# Enable GitHub Pages
gh pages set --branch main --path . --confirm

echo "Repository $REPO_NAME has been created and GitHub Pages enabled."