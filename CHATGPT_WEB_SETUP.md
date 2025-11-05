# ChatGPT Web Integration Setup

This project now supports using the ChatGPT web application (chat.openai.com) as the LLM provider instead of the OpenAI API.

## How It Works

The integration uses Playwright to automate a browser that interacts with ChatGPT's web interface. This allows you to use ChatGPT without needing an API key.

## Setup Instructions

### 1. Install Dependencies

First, install Playwright:

```bash
pip install playwright
playwright install chromium
```

### 2. First-Time Login

When you first use the ChatGPT provider:

1. The system will open a browser window (or run in headless mode if configured)
2. **If a browser window opens**, you'll see ChatGPT's login page
3. Log in to your ChatGPT account manually
4. The system will wait for you to complete login (up to 5 minutes)
5. Your session will be saved in `~/.chatgpt-browser` for future use

### 3. Using the ChatGPT Provider

1. Start the server: `python server.py`
2. Open the frontend in your browser
3. Select "ChatGPT App" from the Provider dropdown
4. Ask your questions - the system will use ChatGPT's web interface

## Configuration

### Headless Mode

By default, the browser runs in **non-headless mode** (visible) so you can see and interact with it. To run in headless mode:

Set environment variable:
```bash
export CHATGPT_HEADLESS=true
```

Or in your `.env` file:
```
CHATGPT_HEADLESS=true
```

### Timeout

The default timeout for waiting for ChatGPT responses is 60 seconds. You can adjust this in the code if needed.

## Important Notes

1. **Login Required**: You must have a ChatGPT account and be logged in
2. **Session Persistence**: Your login session is saved in `~/.chatgpt-browser` - you only need to log in once
3. **Rate Limits**: ChatGPT's web interface may have rate limits or usage restrictions
4. **Page Structure Changes**: If ChatGPT updates their web interface, the selectors may need to be updated
5. **Performance**: Using the web interface is slower than the API because it involves browser automation

## Troubleshooting

### "ChatGPT requires login" Error

- Make sure you're logged into ChatGPT in the browser
- If running in headless mode, try setting `CHATGPT_HEADLESS=false` to see the browser
- Check that the persistent context directory `~/.chatgpt-browser` exists and has proper permissions

### "No response received" Error

- ChatGPT may be slow to respond - try increasing the timeout
- The page structure may have changed - check ChatGPT's website
- Make sure you're not hitting rate limits

### Browser Not Opening

- Check that Playwright is installed: `playwright --version`
- Make sure Chromium is installed: `playwright install chromium`
- Try running with `headless=False` to see what's happening

## Comparison: Web App vs API

| Feature | ChatGPT Web App | OpenAI API |
|---------|----------------|------------|
| Requires API Key | ❌ No | ✅ Yes |
| Requires Login | ✅ Yes | ❌ No |
| Speed | ⚠️ Slower | ✅ Fast |
| Rate Limits | ⚠️ May apply | ✅ Clear limits |
| Cost | ✅ Free (with account) | 💰 Pay per use |
| Reliability | ⚠️ Depends on UI | ✅ Stable |

## Security Note

The persistent browser context stores your ChatGPT session. Make sure to:
- Keep the `~/.chatgpt-browser` directory secure
- Don't share this directory with others
- Be aware that anyone with access to this directory could use your ChatGPT session

