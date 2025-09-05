# Telnyx Contact Center with MCP Analytics

A complete contact center solution built with Telnyx Call Control API and Claude MCP integration. Routes incoming calls through an IVR system to different departments and provides real-time analytics via Claude's Model Context Protocol.

## 🏗️ Architecture

- **Flask Backend**: Handles Telnyx webhooks and call routing
- **SQLite Database**: Stores call events and analytics data  
- **MCP Server**: Exposes analytics to Claude via TypeScript server
- **IVR System**: Routes calls to Sales (1), Support (2), or Porting (3)

## 🚀 Quick Start

### 1. Environment Setup
```bash
git clone <your-repo>
cd telnyx-contact-center-mcp
cp .env.example .env
# Edit .env with your Telnyx API key
```

### 2. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# MCP server dependencies
cd servers/mcp-analytics
npm install
npm run build
cd ../..
```

### 3. Run the Applications

**Terminal 1 - Contact Center Backend:**
```bash
python app.py
# Runs on http://localhost:5000
```

**Terminal 2 - MCP Analytics Server:**
```bash
cd servers/mcp-analytics
node dist/server.js
# Provides analytics tools to Claude
```

**Terminal 3 - Claude CLI with MCP:**
```bash
# Set your custom Anthropic config if needed
export ANTHROPIC_BASE_URL=your_base_url
export ANTHROPIC_AUTH_TOKEN=your_token

# Run Claude with MCP analytics
claude --mcp-config ~/.config/claude/claude_desktop_config.json
```

### 4. Configure Claude MCP
Create `~/.config/claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "telnyx-analytics": {
      "command": "node",
      "args": ["/path/to/your/project/servers/mcp-analytics/dist/server.js"]
    }
  }
}
```

## 📞 How It Works

### Call Flow
1. Customer calls your Telnyx phone number
2. IVR plays: "Press 1 for Sales, 2 for Support, 3 for Porting"
3. System routes call to appropriate SIP endpoint based on selection
4. All events are logged to SQLite database for analytics

### Analytics Tracking
- **Call Volume**: Total inbound calls per department
- **Selection Rate**: % of callers who make IVR selections  
- **Transfer Success**: % of successful call transfers
- **Trends**: Daily call volume patterns

## 🤖 MCP Analytics Tools

Ask Claude these types of questions:

### 📊 KPI Questions
- "What are today's call center KPIs?"
- "Show me sales department metrics for the last 24 hours"
- "What's our IVR selection rate?"
- "How many calls did support handle today?"

### 📈 Trend Questions  
- "Show me call volume trends for the last 7 days"
- "Which day had the most calls this week?"
- "What's the porting department trend over 30 days?"

### 📋 Recent Activity Questions
- "List the last 10 calls with their departments"
- "What calls came in during the last hour?"
- "Show me recent porting requests"
- "Which department got the most recent call?"

### 🎯 Business Questions
- "Which department is busiest?"
- "Are we having transfer problems?"
- "Is our IVR effective?"
- "What's our overall call success rate?"

## 🔧 Configuration

### Environment Variables (.env)
```bash
TELNYX_API_KEY=KEY_your_api_key_here
PORT=5000
FLASK_DEBUG=false

# Department SIP URIs
SALES_SIP_URI=sip:agent1@sip.telnyx.com
SUPPORT_SIP_URI=sip:agent2@sip.telnyx.com  
PORTING_SIP_URI=sip:agent3@sip.telnyx.com

# Database
ANALYTICS_DB=./analytics.sqlite
```

### Telnyx Setup
1. Create a Call Control Application in Telnyx Portal
2. Set webhook URL to `https://your-domain.com/webhook`
3. Link your phone number to the application
4. Configure SIP connections for each department

## 📁 Project Structure

```
├── app.py                    # Main Flask application
├── analytics_db.py          # Database operations
├── analytics_api.py         # HTTP analytics endpoints  
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── SETUP.md               # Detailed setup guide
├── test_mcp.sh           # MCP integration test
├── db/
│   └── schema.sql        # Database schema
└── servers/
    └── mcp-analytics/    # MCP server for Claude integration
        ├── src/
        │   └── server.ts # TypeScript MCP server
        ├── package.json
        └── tsconfig.json
```

## 🧪 Testing

### Test MCP Integration
```bash
./test_mcp.sh
```

### Generate Sample Data
```bash
python -c "
from analytics_db import *
save_call_if_new('test_001', '+15551234567', '+15559876543')
log_ivr_selection('test_001', '1', 'sales')
log_transfer('test_001', 'sip:agent1@sip.telnyx.com', 'success')
print('Test data created')
"
```

### Test Analytics via HTTP
```bash
# Test KPIs
curl "http://localhost:5000/analytics/metrics/kpis" | jq

# Test trends  
curl "http://localhost:5000/analytics/metrics/trend?days=7" | jq

# Test recent calls
curl "http://localhost:5000/analytics/metrics/recent?limit=5" | jq
```

## 🔍 Example Analytics Responses

### 24-Hour KPIs
```json
{
  "window": "24h",
  "department": "all",
  "inbound_volume": 127,
  "selection_rate": 0.834,
  "transfer_success": 0.943
}
```

### Call Volume Trend  
```json
{
  "days": 7,
  "department": "sales",
  "trend": [
    {"day": "2024-01-15", "calls": 23},
    {"day": "2024-01-14", "calls": 19}
  ]
}
```

### Recent Calls
```json
{
  "limit": 5,
  "calls": [
    {
      "call_control_id": "v3:abc123...",
      "department": "support",
      "digit": "2", 
      "ts": "2024-01-15T14:32:18Z"
    }
  ]
}
```

## 🛠️ Development

### Run in Development Mode
```bash
# Flask with debug mode
FLASK_DEBUG=true python app.py

# MCP server with hot reload
cd servers/mcp-analytics
npm run dev
```

### Database Operations
```bash
# View database schema
sqlite3 analytics.sqlite ".schema"

# Check recent calls
sqlite3 analytics.sqlite "SELECT * FROM calls ORDER BY created_at DESC LIMIT 5;"

# Check IVR selections
sqlite3 analytics.sqlite "SELECT * FROM ivr_interactions ORDER BY created_at DESC LIMIT 5;"
```

## 📈 Business Metrics Explained

- **Inbound Volume**: Total calls received (higher = more business activity)
- **Selection Rate**: % who press IVR digits (70-90% is good, lower means confusing IVR)
- **Transfer Success**: % of successful transfers (95%+ is good, lower means technical issues)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test MCP integration with `./test_mcp.sh`
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the SETUP.md guide
2. Test with `./test_mcp.sh`  
3. Review logs in `app.log`
4. Open an issue on GitHub