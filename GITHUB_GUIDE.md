# Complete Guide: Publishing Your Project to GitHub
## (First-Time User Edition)

---

## PART 1 — One-Time Setup (Do This Once)

### Step 1.1 — Create a GitHub Account

1. Go to **https://github.com**
2. Click **"Sign up"** in the top-right corner
3. Enter your email, create a password, and choose a username
4. Verify your email address by clicking the link GitHub sends you

---

### Step 1.2 — Install Git on Your Computer

Git is the software that talks to GitHub from your terminal.

**Windows:**
1. Go to https://git-scm.com/download/win
2. Download and run the installer
3. During setup, accept all defaults (just keep clicking Next → Install)
4. After install, open **Git Bash** (search for it in your Start menu)

**macOS:**
1. Open **Terminal** (search "Terminal" in Spotlight)
2. Type: `git --version`
3. If Git is not installed, macOS will prompt you to install it automatically

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install git -y
```

---

### Step 1.3 — Tell Git Who You Are

Open your terminal (Git Bash on Windows) and run these two commands.
Replace the name and email with your own:

```bash
git config --global user.name "Your Full Name"
git config --global user.email "your@email.com"
```

---

### Step 1.4 — Set Up SSH Authentication (Recommended)

This lets your computer communicate with GitHub securely without typing a password every time.

**Generate an SSH key:**
```bash
ssh-keygen -t ed25519 -C "your@email.com"
```
- Press **Enter** three times to accept all defaults

**Copy your public key:**
```bash
# macOS / Linux:
cat ~/.ssh/id_ed25519.pub

# Windows (Git Bash):
cat ~/.ssh/id_ed25519.pub
```
Select and copy the entire output (starts with `ssh-ed25519 ...`)

**Add the key to GitHub:**
1. Go to **GitHub → Settings** (click your avatar, top-right)
2. Click **"SSH and GPG keys"** in the left sidebar
3. Click **"New SSH key"**
4. Give it a title like "My Laptop"
5. Paste the key you copied
6. Click **"Add SSH key"**

**Test the connection:**
```bash
ssh -T git@github.com
```
You should see: `Hi <username>! You've successfully authenticated...`

---

## PART 2 — Create the Repository on GitHub

### Step 2.1 — Create a New Repository

1. Go to **https://github.com** and log in
2. Click the **"+"** icon in the top-right corner
3. Select **"New repository"**
4. Fill in the form:
   - **Repository name:** `first-break-picking`
   - **Description:** `Automated seismic first-break picking using LightGBM with cross-asset generalisation`
   - **Visibility:** Choose **Public** (so others can find and use your work) or **Private** (only you)
   - **⚠️ IMPORTANT:** Do **NOT** check "Add a README file" or "Add .gitignore" — you already have these
5. Click **"Create repository"**

GitHub will show you a page with setup instructions. **Keep this page open** — you'll need the repository URL in the next step.

---

## PART 3 — Upload Your Project

### Step 3.1 — Extract the Provided ZIP

Unzip the file `first-break-picking.zip` (provided alongside this guide) to a location on your computer, for example:
- `C:\Users\YourName\projects\first-break-picking` (Windows)
- `~/projects/first-break-picking` (macOS / Linux)

### Step 3.2 — Open Terminal in the Project Folder

**Windows:**
- Open **Git Bash**
- Navigate to your project folder:
  ```bash
  cd /c/Users/YourName/projects/first-break-picking
  ```

**macOS / Linux:**
```bash
cd ~/projects/first-break-picking
```

Verify you're in the right place:
```bash
ls
```
You should see files like `README.md`, `config.py`, `requirements.txt`, `scripts/`, etc.

### Step 3.3 — Initialise Git and Make Your First Commit

Run these commands **one line at a time**:

```bash
# Initialise a new git repository in this folder
git init

# Stage all files (the dot means "everything")
git add .

# Check what will be committed
git status

# Create your first commit (a snapshot of your project)
git commit -m "Initial commit: first-break picking pipeline"
```

### Step 3.4 — Connect to GitHub and Push

Replace `<your-username>` with your actual GitHub username:

```bash
# Tell git where your GitHub repository is
git remote add origin git@github.com:<your-username>/first-break-picking.git

# Rename the default branch to "main"
git branch -M main

# Push (upload) your project to GitHub
git push -u origin main
```

When the command finishes, go back to your GitHub repository page and **refresh it** — your files should now be visible!

---

## PART 4 — Verify Everything Looks Right

1. Open **https://github.com/\<your-username\>/first-break-picking**
2. You should see:
   - ✅ Your `README.md` rendered as a nice formatted page
   - ✅ The `scripts/`, `outputs/`, `docs/`, `data/` folders
   - ✅ `config.py`, `requirements.txt`, `.gitignore` in the root
3. Click on `data/` — it should show only `README.md` (no `.hdf5` files — good!)
4. Click on `outputs/evaluation/` — it should have CSV and PNG files, but no huge `predictions_*.csv` files

---

## PART 5 — Making Future Updates

Every time you change something in your project and want to update GitHub:

```bash
# 1. Stage your changes
git add .

# 2. Commit with a descriptive message
git commit -m "Add experiment C results"

# 3. Push to GitHub
git push
```

That's it — no need to repeat the setup steps.

---

## PART 6 — Useful Git Commands Reference

| Command | What it does |
|---|---|
| `git status` | Shows which files have changed |
| `git log --oneline` | Shows a short history of your commits |
| `git diff` | Shows exactly what changed in files |
| `git add <filename>` | Stages a specific file |
| `git add .` | Stages all changed files |
| `git commit -m "message"` | Saves a snapshot with a message |
| `git push` | Uploads your commits to GitHub |
| `git pull` | Downloads any updates from GitHub |

---

## PART 7 — Troubleshooting

**"Permission denied (publickey)"**
→ Your SSH key is not set up correctly. Repeat Step 1.4.

**"remote: Repository not found"**
→ Double-check the URL in your `git remote add` command matches your GitHub username exactly.

**"Everything up-to-date" when pushing**
→ There is nothing new to push. Make a change, then `git add .` and `git commit` first.

**"fatal: not a git repository"**
→ You are not inside the project folder. Use `cd` to navigate there first.

---

## Quick Checklist Before Pushing

- [ ] `README.md` is in the root folder ✅
- [ ] `requirements.txt` is in the root folder ✅
- [ ] `.gitignore` is in the root folder ✅
- [ ] `data/` folder contains only `README.md` (no large `.hdf5` files) ✅
- [ ] `scripts/` folder contains all 10 Python scripts ✅
- [ ] `outputs/` folder contains results, plots, and reports ✅
