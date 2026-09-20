# Git Workflow

This repository uses `origin` for the GitHub repository. A working branch such as `deathpie-main` should normally track `origin/deathpie-main`; `origin/main` is the source branch to merge from.

## Inspect first

```powershell
git status
git remote -v
git branch -vv
```

An `ahead` or `behind` count is relative to the branch's configured upstream. Changing the upstream changes that comparison only; it does not copy commits between branches.

## Sync a working branch

```powershell
git fetch origin
git switch deathpie-main
git merge origin/main
git push origin deathpie-main
```

Replace `deathpie-main` with the actual working branch. Keep the working branch's upstream pointed at its matching remote branch so normal status and push behavior remain clear. Do not set it to `origin/main` merely to hide a behind count.

## GitHub identity

For HTTPS remotes, check the GitHub CLI identity before changing remotes or branch tracking:

```powershell
gh auth status
gh auth switch --hostname github.com --user <github-account>
gh auth setup-git
```

Use the account that has permission to push to the repository. Never put passwords, personal access tokens, or credential-manager contents in this repository or in a command copied into documentation.

## Agent boundary

AI agents may inspect Git state, history, diffs, remotes, and ignore behavior. They must not stage, commit, push, reset, clean, checkout, or revert repository changes unless the maintainer explicitly requests that operation. A maintainer should review the diff and run the repository validator before uploading changes.
