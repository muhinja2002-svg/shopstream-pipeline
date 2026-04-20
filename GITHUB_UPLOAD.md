# Uploading ShopStream to GitHub

Follow these steps in your terminal from inside the `shopstream/` folder.

---

## Step 1 — Create the repo on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Set the repository name to `shopstream`
3. Leave it **Public** (so recruiters can find it)
4. **Do NOT** tick "Add a README" — we already have one
5. Click **Create repository**

GitHub will show you a page with the repo URL — copy it. It looks like:
```
https://github.com/YOUR_USERNAME/shopstream.git
```

---

## Step 2 — Initialise git and make your first commit

Run these commands one at a time from inside your project folder:

```bash
# Initialise a new git repository
git init

# Stage all project files
git add .

# Verify what's being committed (optional but recommended)
git status

# Make the first commit
git commit -m "feat: initial ShopStream real-time pipeline

- Redpanda (Kafka-compatible) event streaming via Docker
- Python producer with session-based event generation
- Python consumer with validation and DuckDB persistence
- dbt staging + mart models with data quality tests
- Streamlit live analytics dashboard with funnel + time-series charts"
```

---

## Step 3 — Connect to GitHub and push

```bash
# Add your GitHub repo as the remote origin
# Replace YOUR_USERNAME with your actual GitHub username
git remote add origin https://github.com/YOUR_USERNAME/shopstream.git

# Rename the default branch to 'main'
git branch -M main

# Push to GitHub
git push -u origin main
```

Your project is now live at `https://github.com/YOUR_USERNAME/shopstream`.

---

## Step 4 — Add a description and topics on GitHub

After pushing, go to your repo page on GitHub and click the gear icon next to "About":

- **Description:** Real-time e-commerce analytics pipeline using Redpanda, DuckDB, dbt, and Streamlit
- **Topics:** `data-engineering`, `kafka`, `duckdb`, `dbt`, `streamlit`, `python`, `redpanda`, `portfolio`

Topics make your project discoverable when recruiters search GitHub.

---

## Making future updates

After any code changes:

```bash
git add .
git commit -m "your message here"
git push
```

### Commit message conventions (good habit for your CV)

| Prefix | Use for |
|--------|---------|
| `feat:` | New features |
| `fix:` | Bug fixes |
| `docs:` | README or comment changes |
| `refactor:` | Code restructuring without behaviour change |
| `test:` | Adding or fixing tests |

Example: `git commit -m "feat: add SKU revenue breakdown to dashboard"`

---

## Troubleshooting

**`git push` asks for a password**
GitHub no longer accepts passwords. Use a Personal Access Token:
1. GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Generate a token with `repo` scope
3. Use that token as your "password" when prompted

**Or use SSH (recommended long-term):**
```bash
# Generate an SSH key
ssh-keygen -t ed25519 -C "your@email.com"

# Copy the public key
cat ~/.ssh/id_ed25519.pub

# Paste it at: GitHub → Settings → SSH and GPG keys → New SSH key

# Change your remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/shopstream.git
```
