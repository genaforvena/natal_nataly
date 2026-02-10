# CI/CD Quick Setup Checklist

This is a quick reference for setting up and maintaining CI/CD checks for the natal_nataly repository.

## ✅ Initial Setup (One-Time)

### For Repository Administrators

- [ ] **Enable Branch Protection for `main` branch**
  1. Go to: https://github.com/genaforvena/natal_nataly/settings/branches
  2. Click "Add branch protection rule"
  3. Branch name pattern: `main`
  4. Check: ✅ Require a pull request before merging
  5. Check: ✅ Require status checks to pass before merging
  6. Select these required checks:
     - `lint`
     - `test`
     - `docker-build`
     - `all-checks` (recommended)
  7. Check: ✅ Require branches to be up to date before merging
  8. Check: ✅ Require conversation resolution before merging
  9. Check: ✅ Include administrators
  10. Click "Create" or "Save changes"

- [ ] **Optional: Enable Branch Protection for `development` branch**
  - Follow same steps but use pattern: `development`
  - Consider more lenient settings (fewer required approvals)

- [ ] **Verify CI Badge in README**
  - Check that the CI badge shows "passing" status
  - Badge URL: https://github.com/genaforvena/natal_nataly/actions/workflows/ci.yml/badge.svg

## 📋 Developer Workflow

### Before Creating a PR

```bash
# 1. Run tests locally
pytest tests/ -v

# 2. Run linting
flake8 .

# 3. Run type checking (optional)
mypy . --config-file mypy.ini

# 4. Check coverage (optional)
pytest tests/ --cov=. --cov-report=term-missing
```

### Creating a PR

1. Push your branch to GitHub
2. Open pull request to `main` (or `development`)
3. Wait for CI checks to run (2-3 minutes)
4. Address any failures before requesting review
5. Once checks pass and reviews are approved, merge!

## 🔧 Maintenance Tasks

### Adding a New CI Check

1. Edit `.github/workflows/ci.yml`
2. Add new job following existing pattern
3. Add job to `needs` array in `all-checks` job
4. Push changes and verify workflow runs
5. Update branch protection to require new check

### Updating Status Check Requirements

1. Go to Settings > Branches
2. Edit the branch protection rule
3. Add/remove checks from required list
4. Save changes

### Responding to CI Failures

**Lint Failures:**
```bash
flake8 .  # See all issues
# Fix issues or add to .flake8 ignore list
```

**Test Failures:**
```bash
pytest tests/ -v --tb=short  # See failure details
# Fix the test or code
# Re-run to verify fix
```

**Docker Build Failures:**
```bash
docker build -t natal-nataly:test .  # Test locally
# Fix Dockerfile or dependencies
```

### Monthly Maintenance

- [ ] Review and update dependencies
  ```bash
  pip list --outdated
  ```
- [ ] Check for security vulnerabilities
  ```bash
  safety check
  ```
- [ ] Review CI run times and optimize if needed
- [ ] Update CI dependencies (setup-python, checkout actions)

## 📊 Monitoring

### Check CI Health

- View recent workflow runs: https://github.com/genaforvena/natal_nataly/actions
- Look for patterns in failures
- Monitor run times for performance issues

### Status Check Reference

| Check | Duration | Purpose |
|-------|----------|---------|
| `lint` | ~30s | Code style validation |
| `type-check` | ~45s | Static type checking |
| `test` | ~1-2min | Unit & integration tests |
| `docker-build` | ~1min | Docker image verification |
| `security-scan` | ~30s | Dependency vulnerabilities |
| `all-checks` | ~10s | Aggregation of results |

**Total CI Time:** ~2-3 minutes for full pipeline

## 🚨 Emergency Procedures

### Bypass Checks (Critical Hotfix Only)

⚠️ **Use only in emergencies!**

1. Repository admin goes to Settings > Branches
2. Edit branch protection rule for `main`
3. Temporarily uncheck "Require status checks to pass before merging"
4. Merge the critical fix
5. **Immediately re-enable the setting**
6. Document why bypass was necessary in PR comments

### CI System Down

If GitHub Actions is down:

1. Check: https://www.githubstatus.com
2. Wait for service restoration
3. Run all checks locally before merging
4. Document in PR that manual verification was performed

## 📚 Documentation

For detailed information, see:

- [BRANCH_PROTECTION_SETUP.md](BRANCH_PROTECTION_SETUP.md) - Full setup guide
- [TESTING.md](TESTING.md) - Testing and CI/CD details
- [CI_CD_IMPLEMENTATION.md](CI_CD_IMPLEMENTATION.md) - Implementation reference

## ✨ Best Practices

1. ✅ **Always run tests locally before pushing**
2. ✅ **Keep PR size small** (easier to review and test)
3. ✅ **Don't merge with failing checks** (use the system as designed)
4. ✅ **Fix flaky tests immediately** (don't let them accumulate)
5. ✅ **Review CI logs for warnings** (even on passing runs)
6. ✅ **Update documentation** when changing workflows
7. ✅ **Communicate CI changes** to the team

## 🎯 Success Metrics

Your CI/CD is working well if:

- ✅ 95%+ of PRs pass on first attempt
- ✅ CI runs complete in < 5 minutes
- ✅ No bypassing of checks needed
- ✅ Failures are caught before manual review
- ✅ Main branch stays green
- ✅ Team trusts the CI results

---

Last updated: 2026-02-10
