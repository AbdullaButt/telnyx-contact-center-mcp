# Detailed Setup Guide

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Telnyx account with API key
- ngrok (for local webhook testing)

## Step-by-Step Setup

### 1. Project Setup
```bash
git clone <your-repo-url>
cd telnyx-contact-center-mcp
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` file:
```bash
TELNYX_API_KEY=KEY_your_actual_telnyx_api_key_here
SALES_SIP_URI=sip:sales@yourdomain.com
SUPPORT_SIP_URI=sip:support@yourdomain.com  
PORTING_SIP_URI=sip:porting@yourdomain.com
```

### 3. Install Dependencies

**Python Flask App:**
```bash
pip install -r requirements.txt
```

**MCP Analytics Server:**
```bash
cd servers/mcp-analytics
npm install
npm run build
cd ../..
```

### 4. Initialize Database
```bash
python -c "from analytics_db import init_db; init_db(); print('Database ready')"
```

### 5. Configure Telnyx

1. **Create Call Control Application:**
   - Login to Telnyx Portal
   - Go to "Call Control" → "Applications"
   - Create new application
   - Set webhook URL to your public URL + `/webhook`

2. **Configure Phone Number:**
   - Go to "Phone Numbers" → "My Numbers"
   - Edit your DID number
   - Set connection to your Call Control Application

3. **Set up SIP Endpoints:**
   - Create SIP connections for each department
   - Configure SIP clients (like Zoiper) with credentials

### 6. Configure Claude MCP

**For Claude CLI:**
```bash
mkdir -p ~/.config/claude
cat > ~/.config/claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "telnyx-analytics": {
      "command": "node", 
      "args": ["/full/path/to/your/project/servers/mcp-analytics/dist/server.js"]
    }
  }
}
EOF
```

**For Claude Desktop (Windows/Mac):**
Add the same config to Claude Desktop's MCP settings.

### 7. Running the System

**Terminal 1 - Flask Backend:**
```bash
python app.py
# Starts webhook server on port 5000
```

**Terminal 2 - Expose via ngrok (if local):**
```bash
ngrok http 5000
# Use the HTTPS URL in your Telnyx webhook config
```

**Terminal 3 - MCP Analytics Server:**
```bash
cd servers/mcp-analytics
node dist/server.js
# Provides analytics tools to Claude
```

**Terminal 4 - Claude CLI with MCP:**
```bash
# Optional: Set custom Anthropic endpoints
export ANTHROPIC_BASE_URL=your_custom_url
export ANTHROPIC_AUTH_TOKEN=your_token

claude --mcp-config ~/.config/claude/claude_desktop_config.json
```

### 8. Test the Integration
```bash
./test_mcp.sh
```

## Available MCP Tools

- **`get_kpis`** - 24h call center KPIs (volume, selection rate, transfer success)
- **`get_trend`** - Daily call volume trends over N days
- **`list_calls`** - Recent calls with IVR selections and routing info
- **`analytics://dashboard_24h`** - Complete dashboard resource

## Troubleshooting

### Common Issues

**MCP Server won't start:**
```bash
cd servers/mcp-analytics
npm run build
node dist/server.js
```

**Database issues:**
```bash
rm analytics.sqlite
python -c "from analytics_db import init_db; init_db()"
```

**No call data:**
- Check webhook URL in Telnyx is correct
- Verify ngrok tunnel is active
- Check `app.log` for webhook events

**Claude can't connect to MCP:**
- Verify config file path is correct
- Check MCP server is running
- Test with `./test_mcp.sh`

### Testing Without Real Calls
```bash
python -c "
from analytics_db import *
import time

# Generate test data
calls = [('test_1', '+15551111', '+15559999', 'sales', '1'),
         ('test_2', '+15552222', '+15559999', 'support', '2')]

for cid, from_num, to_num, dept, digit in calls:
    save_call_if_new(cid, from_num, to_num)
    log_ivr_selection(cid, digit, dept)
    log_transfer(cid, f'sip:{dept}@example.com', 'success')
    time.sleep(0.1)
print('Test data created')
"
```

## Production Deployment

### Security
- Use environment variables for secrets
- Enable HTTPS for webhooks
- Set up proper firewall rules
- Consider webhook signature verification

### Monitoring  
- Monitor `analytics.sqlite` file growth
- Set up log rotation for `app.log`
- Monitor MCP server uptime
- Track webhook response times

### Scaling
- Consider PostgreSQL for high volume
- Use Redis for session management
- Deploy behind load balancer
- Set up database backups