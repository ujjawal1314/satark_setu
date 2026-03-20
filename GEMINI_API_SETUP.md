# 🤖 Gemini API Setup Guide

## Quick Setup (3 Steps)

### Step 1: Get Your API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key (starts with `AIza...`)

### Step 2: Configure the .env File

1. Open the file: `SatarkSetu/.env`
2. Find this line:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
3. Replace `your_api_key_here` with your actual API key:
   ```
   GEMINI_API_KEY=AIzaSyABC123def456GHI789jkl012MNO345pqr
   ```
4. Save the file

### Step 3: Restart the Dashboard

If the dashboard is already running:
1. Press `Ctrl+C` to stop it
2. Run again: `streamlit run dashboard_enhanced.py`

If not running yet:
```bash
streamlit run dashboard_enhanced.py
```

---

## ✅ Verify It's Working

### Test 1: Check Console Output
When you start the dashboard, you should NOT see:
```
⚠️ GEMINI_API_KEY not found. Using fallback explanations.
```

### Test 2: Generate AI Explanation
1. Open the dashboard
2. Go to "Ring Analysis" view
3. Select any ring
4. Click "🤖 Generate AI Explanation"
5. You should see a detailed, natural language explanation

### Test 3: Account Lookup
1. Go to "Account Lookup" view
2. Enter: `ACC_002747`
3. Scroll down to see AI explanation
4. Should be detailed and contextual

---

## 🔒 Security Notes

### Keep Your API Key Safe
- ✅ The `.env` file is already in `.gitignore`
- ✅ Never commit `.env` to version control
- ✅ Never share your API key publicly
- ✅ Regenerate key if accidentally exposed

### API Key Permissions
Your key has access to:
- Gemini 1.5 Flash model
- Text generation only
- No access to your Google account data

---

## 💰 Pricing Information

**Gemini 1.5 Flash Pricing:**
- Input: $0.075 per 1 million tokens
- Output: $0.30 per 1 million tokens

**Estimated Usage:**
- Per explanation: ~500 input tokens, ~200 output tokens
- Cost per explanation: ~$0.0001 (less than 1 cent)
- 1,000 explanations: ~$0.10
- Very affordable for testing and demos!

**Free Tier:**
- 15 requests per minute
- 1 million tokens per day
- More than enough for demos

---

## 🔧 Troubleshooting

### Issue: "GEMINI_API_KEY not found"

**Solution 1:** Check .env file exists
```bash
# Windows
dir .env

# Should show the file
```

**Solution 2:** Check .env file content
```bash
# Windows
type .env

# Should show: GEMINI_API_KEY=AIza...
```

**Solution 3:** Verify no extra spaces
```
# WRONG (space before key)
GEMINI_API_KEY= AIzaSy...

# CORRECT (no spaces)
GEMINI_API_KEY=AIzaSy...
```

### Issue: "API key invalid"

**Solution:** Regenerate key
1. Go to: https://makersuite.google.com/app/apikey
2. Delete old key
3. Create new key
4. Update .env file
5. Restart dashboard

### Issue: "Rate limit exceeded"

**Solution:** You're making too many requests
- Free tier: 15 requests/minute
- Wait 1 minute and try again
- Or upgrade to paid tier

### Issue: Still using fallback mode

**Check:**
1. API key is correct in .env
2. No quotes around the key
3. File is named exactly `.env` (not `.env.txt`)
4. Dashboard was restarted after editing .env

---

## 🎯 What Changes With Real API

### Without API Key (Fallback Mode):
- ✅ System works perfectly
- ✅ Rule-based explanations
- ✅ Template-driven responses
- ❌ Less natural language
- ❌ Less contextual

### With API Key (Gemini Mode):
- ✅ Natural language explanations
- ✅ Highly contextual
- ✅ Adapts to specific patterns
- ✅ More detailed insights
- ✅ Better victim scenarios
- ✅ More professional

---

## 📝 Example .env File

```bash
# SatarkSetu - Environment Configuration

# Gemini API Key
GEMINI_API_KEY=AIzaSyABC123def456GHI789jkl012MNO345pqr

# Optional: Add other config here in future
# DATABASE_URL=postgresql://localhost/satarksetu
# REDIS_URL=redis://localhost:6379
```

---

## 🚀 Quick Test Script

Create a test file to verify API key works:

```python
# test_gemini.py
from gemini_explainer import GeminiExplainer

explainer = GeminiExplainer()

if explainer.model:
    print("✅ Gemini API configured successfully!")
    print("🤖 Testing explanation generation...")
    
    test_data = {
        'account_id': 'TEST_001',
        'risk_score': 85
    }
    
    explanation = explainer.explain_mule_pattern(
        test_data,
        ['malware', 'foreign_ip'],
        ['rapid_transactions'],
        None
    )
    
    print("\n📝 Generated Explanation:")
    print(explanation)
else:
    print("❌ Gemini API not configured")
    print("Using fallback mode")
```

Run:
```bash
python test_gemini.py
```

---

## ✅ Checklist

- [ ] Got API key from Google AI Studio
- [ ] Created/edited `.env` file
- [ ] Pasted API key (no quotes, no spaces)
- [ ] Saved `.env` file
- [ ] Restarted dashboard
- [ ] Tested AI explanation
- [ ] Verified natural language output

---

## 🎉 You're All Set!

Your SatarkSetu system now has:
- ✅ Real Gemini AI integration
- ✅ Natural language explanations
- ✅ Enhanced insights
- ✅ Professional output

**Next:** Run the dashboard and try the AI features!

```bash
streamlit run dashboard_enhanced.py
```

---

**Need Help?**
- API Key Issues: https://ai.google.dev/gemini-api/docs/api-key
- Gemini Docs: https://ai.google.dev/gemini-api/docs
- Project Docs: See README.md

🛡️ **SatarkSetu - Now with AI Power!**
