# 🤖 Auto GitHub Contributions Setup

Sistem otomatis untuk membuat contributions di GitHub setiap 30 menit tanpa manual intervention.

## 🎯 Tujuan

- ✅ **Fully Automatic**: Berjalan setiap 30 menit tanpa manual
- ✅ **GitHub Contributions**: Terhitung di contribution graph
- ✅ **AI Test Generation**: Generate test cases otomatis dengan Gemini
- ✅ **Meaningful Commits**: Bukan spam, tapi actual improvements

## 🚀 Quick Setup (5 menit)

### 1. Add GitHub Secrets

Di repository GitHub anda, masuk ke **Settings > Secrets and variables > Actions**, lalu add:

```
GEMINI_API_KEY = your-gemini-api-key-here
```

**Optional**: Jika anda ingin contributions lebih personal, add juga:
```
PERSONAL_ACCESS_TOKEN = your-github-personal-access-token
```

### 2. Enable GitHub Actions

- Pastikan **Actions** enabled di repository settings
- Workflow akan otomatis start setelah setup

### 3. Verify Setup

Run test secara manual untuk memastikan semua berjalan:

```bash
cd ai-product-qa
python .github/scripts/test_auto_workflow.py
```

### 4. Monitor Results

- Check **Actions** tab di GitHub repository
- Lihat commits baru setiap 30 menit
- Monitor contribution graph (mungkin butuh beberapa jam)

## 📋 How It Works

### Auto Schedule
```yaml
schedule:
  - cron: '*/30 * * * *'  # Every 30 minutes
```

### Workflow Steps
1. **Coverage Analysis**: Scan kode untuk test coverage rendah
2. **AI Test Generation**: Generate test cases dengan Gemini AI
3. **Contribution Bot**: Update activity log dan README stats
4. **Auto Commit**: Commit dan push perubahan

### Git Attribution
```bash
# Otomatis menggunakan repository owner
user.name = "your-github-username"
user.email = "your-github-username@users.noreply.github.com"
```

## 🔧 Customization

### Change Frequency

Edit `.github/workflows/auto-commit.yml`:

```yaml
schedule:
  - cron: '*/15 * * * *'  # Every 15 minutes
  - cron: '0 */2 * * *'   # Every 2 hours  
  - cron: '0 9,17 * * 1-5' # 9 AM & 5 PM, weekdays only
```

### Customize Commit Messages

Edit `.github/scripts/contribution_bot.py`:

```python
commit_msg = f"🤖 Auto-update: Custom message - {timestamp}"
```

### Configure Test Generation

Edit `.github/scripts/config.py`:

```python
TEST_GENERATION_SETTINGS = {
    "model": "gemini-2.0-flash-experimental",
    "max_retries": 3,
    "min_coverage_threshold": 80.0,
    "max_files_per_run": 3  # Reduce untuk less activity
}
```

## 📊 Expected Results

### Commits
- **Frequency**: Every 30 minutes (jika ada changes)
- **Content**: Test files, activity logs, README updates
- **Attribution**: Proper username untuk contributions

### Files Created/Updated
- `bot_activity.json` - Activity tracking
- `README.md` - Stats section dengan bot activity
- `tests/test_*.py` - Generated test files
- `coverage_report.json` - Coverage analysis results

### Example Commit Messages
```
🤖 Auto-update: Test coverage improvement - 2025-06-28 15:30 UTC
🤖 Auto-update: AI test generation and coverage improvement - 2025-06-28 16:00 UTC
```

## 🐛 Troubleshooting

### No Contributions Showing
```bash
# Check git user config in workflow logs
# Should show: your-username@users.noreply.github.com
```

### No Commits Being Made
1. Check if workflow is running (Actions tab)
2. Verify GEMINI_API_KEY is set
3. Check workflow logs for errors

### Test Generation Failing
```bash
# Manual test
export GEMINI_API_KEY="your-key"
python .github/scripts/test_generator.py
```

### Contributions Not Counting
- Repository must be **public** atau anda **collaborator**
- Commits must be on **default branch** (main/master)
- Email must match your **GitHub account**
- May take **2-24 hours** to appear

## 🎯 Success Criteria

After setup, you should see:

- ✅ Workflow running every 30 minutes in Actions tab
- ✅ New commits appearing automatically  
- ✅ Green squares in your contribution graph
- ✅ Updated bot_activity.json with increasing commit count
- ✅ README with bot stats section

## 🔄 Manual Control

### Force Run Now
- Go to **Actions** tab
- Click **AI Test Generation Auto-Commit**
- Click **Run workflow**

### Pause Auto-Commits
```yaml
# Comment out schedule in .github/workflows/auto-commit.yml
# schedule:
#   - cron: '*/30 * * * *'
```

### Emergency Stop
- Disable workflow di **Actions** tab
- Or delete `.github/workflows/auto-commit.yml`

## 💡 Pro Tips

### Maximize Contributions
1. **Use Personal Email**: Add your real email untuk more attribution
2. **Multiple Repositories**: Setup di beberapa repos
3. **Peak Hours**: Schedule saat activity tinggi (weekdays 9-17)

### Optimize Performance
1. **Reduce Frequency**: Ganti ke 60 minutes untuk less resource usage
2. **Limit Files**: Set max_files_per_run = 2
3. **Skip Weekends**: Use cron pattern untuk weekdays only

### Monitor Health
```bash
# Check workflow status
gh workflow list
gh run list --workflow=auto-commit.yml

# Monitor logs
gh run view --log
```

---

## 🎉 You're All Set!

Sistem sekarang akan berjalan otomatis setiap 30 menit dan membuat meaningful contributions yang terhitung di GitHub profile anda. 

**No manual intervention required!** ✨

*Last updated: 2025-06-28* 