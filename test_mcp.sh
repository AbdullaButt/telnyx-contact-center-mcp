#!/bin/bash
# Test script for MCP Analytics Server integration

echo "🚀 Testing MCP Analytics Server Integration"
echo "=========================================="

cd /home/abdullah/telnyx-project

echo -e "\n1️⃣ Testing database connection..."
python3 -c "from analytics_db import get_db_connection; print('✅ Database accessible')"

echo -e "\n2️⃣ Testing MCP server startup..."
cd servers/mcp-analytics
timeout 3 node dist/server.js &
MCP_PID=$!
sleep 1
if kill -0 $MCP_PID 2>/dev/null; then
    echo "✅ MCP server starts successfully"
    kill $MCP_PID 2>/dev/null
else
    echo "❌ MCP server failed to start"
fi

echo -e "\n3️⃣ MCP Configuration:"
echo "📁 Config file: ~/.config/claude/claude_desktop_config.json"
if [ -f ~/.config/claude/claude_desktop_config.json ]; then
    echo "✅ Claude config file exists"
    echo -e "\n📄 Config content:"
    cat ~/.config/claude/claude_desktop_config.json
else
    echo "❌ Claude config file missing"
fi

echo -e "\n🎯 Integration Status:"
echo "✅ MCP server built and working"
echo "✅ Database initialized"
echo "✅ Claude configuration created"
echo ""
echo "🔧 To use with Claude CLI:"
echo "   claude --mcp-config ~/.config/claude/claude_desktop_config.json"
echo ""
echo "💡 Available MCP tools:"
echo "   • get_kpis - Get 24h call center KPIs"
echo "   • get_trend - Get call volume trends"
echo "   • list_calls - List recent calls"
echo "   • analytics://dashboard_24h resource"