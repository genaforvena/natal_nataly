# Branch Protection Setup Guide

This guide explains how to enable branch protection rules to make CI/CD checks mandatory for all pull requests before merging.

## Overview

Branch protection rules ensure that all pull requests pass the required CI/CD checks before they can be merged into protected branches (typically `main` and `development`). This prevents broken code from being merged and maintains code quality.

## Prerequisites

- You must have **admin access** to the repository
- CI/CD workflow must be set up (already done in `.github/workflows/ci.yml`)
- At least one successful workflow run on the branch you want to protect

## Step-by-Step Setup

### 1. Navigate to Branch Protection Settings

1. Go to the repository on GitHub: https://github.com/genaforvena/natal_nataly
2. Click on **Settings** (top menu bar)
3. In the left sidebar, click on **Branches**
4. Under "Branch protection rules", click **Add rule** or **Add branch protection rule**

### 2. Configure Protection for Main Branch

#### Basic Settings

1. **Branch name pattern**: Enter `main`
2. Check the following options:

#### Require Pull Request Before Merging
- ✅ **Require a pull request before merging**
  - Number of required approvals: `1` (or more based on team size)
  - ✅ **Dismiss stale pull request approvals when new commits are pushed**
  - ✅ **Require review from Code Owners** (optional, if you have CODEOWNERS file)

#### Require Status Checks to Pass Before Merging
- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**
  
  **Select the following required status checks:**
  - `lint` - Ensures code passes flake8 linting
  - `type-check` - Ensures code passes mypy type checking (optional)
  - `test` - Ensures all tests pass with coverage
  - `docker-build` - Ensures Docker image builds successfully
  - `all-checks` - Aggregated check that ensures all required checks passed

  > **Note**: Status checks will only appear in this list after they have run at least once on the branch. If you don't see them, trigger a workflow run first by pushing a commit or opening a PR.

#### Additional Recommended Settings
- ✅ **Require conversation resolution before merging** - Ensures all PR comments are resolved
- ✅ **Require linear history** - Prevents merge commits (optional, enforces rebase/squash)
- ✅ **Include administrators** - Applies rules to repository admins as well (recommended)
- ✅ **Restrict who can push to matching branches** - Only allow specific people/teams to push directly (optional)

#### Rules Applied to Everyone
- ✅ **Allow force pushes** - Keep this **unchecked** to prevent force pushes
- ✅ **Allow deletions** - Keep this **unchecked** to prevent branch deletion

### 3. Configure Protection for Development Branch (Optional)

Repeat the same steps for the `development` branch if you want to protect it as well. You may choose to:
- Require fewer approvals (e.g., 0 or 1)
- Make status checks required but not require branches to be up to date
- Skip some optional checks

### 4. Save the Branch Protection Rule

1. Scroll to the bottom of the page
2. Click **Create** (or **Save changes** if editing existing rule)

## Verifying Branch Protection

### Test the Setup

1. Create a new branch: `git checkout -b test-branch-protection`
2. Make a small change to any file
3. Commit and push: `git commit -am "Test branch protection" && git push origin test-branch-protection`
4. Open a pull request to `main`
5. Observe that:
   - CI/CD checks automatically start running
   - You cannot merge until all required checks pass
   - The "Merge" button is disabled until checks complete

### Expected Behavior

When branch protection is enabled:

✅ **Pull Request Opened**
- CI/CD pipeline automatically runs
- Status checks show as "In Progress"
- Merge button is disabled

✅ **Checks Running**
- Lint, test, docker-build, and other checks execute in parallel
- You can view real-time progress in the PR "Checks" tab
- Any failures are clearly marked

✅ **Checks Passed**
- All required checks show green checkmarks
- "Merge" button becomes enabled
- PR can now be merged (if reviews are also approved)

❌ **Checks Failed**
- Failed checks show red X marks
- Merge button remains disabled
- Details of failures are available in check logs
- Must fix issues and push new commits to re-run checks

## Status Check Reference

Here's what each required status check validates:

| Check | Purpose | Blocking | Configuration |
|-------|---------|----------|---------------|
| `lint` | Code style and formatting (flake8) | Yes | `.flake8` |
| `type-check` | Static type checking (mypy) | No* | `mypy.ini` |
| `test` | Unit and integration tests | Yes | `pytest.ini` |
| `docker-build` | Verifies Docker image builds | Yes | `Dockerfile` |
| `security-scan` | Dependency vulnerability scan | No* | N/A |
| `all-checks` | Aggregates all required checks | Yes | N/A |

\* *Currently set to advisory only (`continue-on-error: true`)*

## Troubleshooting

### Status Checks Don't Appear in the List

**Problem**: When setting up branch protection, the required status checks don't show up in the dropdown.

**Solution**: 
1. Ensure the CI workflow has run at least once on the branch you're protecting
2. Push a commit to trigger the workflow, or manually trigger it from Actions tab
3. Wait for the workflow to complete
4. Refresh the branch protection settings page
5. The status checks should now appear in the dropdown

### Cannot Merge Despite Passing Checks

**Problem**: All checks pass but merge button is still disabled.

**Solutions**:
- Check if pull request reviews are required and not yet approved
- Verify all conversations are resolved (if that setting is enabled)
- Ensure branch is up to date with base branch (if that setting is enabled)
- Check if there are merge conflicts that need resolution

### Checks Keep Failing

**Problem**: CI/CD checks consistently fail on PRs.

**Solutions**:
1. Review the specific check that's failing in the Actions tab
2. Run checks locally before pushing:
   ```bash
   # Run linting
   flake8 .
   
   # Run tests
   pytest tests/ -v
   
   # Run type checking
   mypy . --config-file mypy.ini
   
   # Build Docker image
   docker build -t natal-nataly:test .
   ```
3. Fix issues locally and push again
4. Review the [TESTING.md](TESTING.md) guide for detailed troubleshooting

### Need to Bypass Checks (Emergency)

**Problem**: Critical hotfix needed but checks are failing due to unrelated issues.

**Options**:
1. **Recommended**: Fix the failing checks first
2. **If urgent**: Repository admin can temporarily disable branch protection
   - Go to Settings > Branches
   - Edit the branch protection rule
   - Uncheck "Require status checks to pass before merging"
   - Merge the PR
   - **Re-enable the protection immediately after**
3. **Alternative**: Admin can use "Bypass branch protections" permission if configured

> ⚠️ **Warning**: Bypassing checks should be a last resort and documented in the PR.

## Maintenance

### Updating Required Checks

When adding new jobs to the CI workflow:

1. Add the job to `.github/workflows/ci.yml`
2. Push changes and let the workflow run once
3. Go to branch protection settings
4. Add the new job name to required status checks
5. Save the branch protection rule

### Removing Outdated Checks

If a job is removed from the workflow:

1. Go to branch protection settings
2. Find the outdated check in the required list
3. Click the X to remove it
4. Save the branch protection rule

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Status Checks Documentation](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- [CI/CD Implementation Details](CI_CD_IMPLEMENTATION.md)
- [Testing Guide](TESTING.md)

## Summary

Once branch protection is enabled with required status checks:

✅ All PRs must pass CI/CD checks before merging
✅ Code quality is automatically enforced
✅ Broken code cannot be merged
✅ Team maintains high standards without manual oversight
✅ Confidence in the main branch is maintained

**Next Step**: Follow the setup instructions above to enable branch protection for your repository!
