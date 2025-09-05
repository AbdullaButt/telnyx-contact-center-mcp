# Claude MCP Analytics Questions Guide

This guide shows exactly what questions you can ask Claude when the MCP analytics server is running.

## 📊 Key Performance Indicators (KPIs)

### Basic KPI Questions
- "Get today's call center KPIs"
- "Show me 24-hour metrics" 
- "What are our current performance indicators?"
- "Display overall contact center stats"

### Department-Specific KPIs
- "Show me sales department KPIs"
- "What are support's metrics for today?"
- "Get porting department performance"
- "Compare all three departments"

### KPI Analysis Questions
- "What's our IVR selection rate?"
- "How successful are our call transfers?"
- "What's the inbound call volume today?"
- "Are callers engaging with our IVR?"

## 📈 Trend Analysis

### Basic Trend Questions
- "Show call volume trends for the last 7 days"
- "What's our weekly call pattern?"
- "Display daily call trends"
- "Show me call volume over time"

### Department Trend Questions
- "Show sales call trends for the last 14 days"
- "What's the support department trend?"
- "Display porting calls over the last month"
- "Compare department trends"

### Specific Time Periods
- "Show trends for the last 3 days"
- "What's our 30-day call pattern?"
- "Display call volume for the past week"
- "Show me yesterday vs today trends"

## 📋 Recent Call Activity

### Basic Recent Call Questions
- "List the last 10 calls"
- "Show me recent call activity"
- "What calls came in recently?"
- "Display the most recent calls"

### Department-Specific Recent Calls
- "Show recent sales calls"
- "List support department calls"
- "What porting calls came in today?"
- "Show me recent calls by department"

### Specific Limits
- "List the last 5 calls"
- "Show me 20 recent calls" 
- "Display the last 50 calls"
- "Get recent calls with limit 3"

## 🎯 Business Intelligence Questions

### Performance Analysis
- "Which department is busiest?"
- "What department gets the most calls?"
- "Are we having transfer issues?"
- "Is our IVR working effectively?"

### Operational Questions  
- "How many calls did we miss selections on?"
- "What's our call success rate?"
- "Are transfers failing?"
- "Which department has the best metrics?"

### Time-Based Analysis
- "What was our busiest day this week?"
- "When do we get the most calls?"
- "Which day had the most sales calls?"
- "What's our peak call period?"

## 📊 Dashboard and Summary Questions

### Full Dashboard
- "Show me the complete analytics dashboard"
- "Get a full overview of all metrics"
- "Display comprehensive call center data"
- "Show me everything about today's performance"

### Summary Questions
- "Summarize today's call center activity"
- "Give me a quick overview of performance" 
- "What's happening with our calls today?"
- "Brief me on call center metrics"

## 🔍 Specific Investigative Questions

### Problem Identification
- "Are callers hanging up without selecting?"
- "Why is our selection rate low?"
- "What's causing transfer failures?"
- "Which department has issues?"

### Comparative Analysis
- "Compare today vs yesterday"
- "How do departments stack up?"
- "Which metrics are improving?"
- "What trends are concerning?"

### Drill-Down Questions
- "Show me details for the sales department"
- "Break down transfer success by department"
- "What specific calls had issues?"
- "Which calls didn't complete transfers?"

## 🤖 Example Claude Conversations

### Getting Started
```
You: "Get today's call center KPIs"
Claude: [Uses get_kpis tool and shows metrics]

You: "Which department is busiest?"
Claude: [Analyzes KPI data and compares departments]
```

### Trend Analysis
```
You: "Show call trends for the last week"
Claude: [Uses get_trend tool with days=7]

You: "What's the pattern?"
Claude: [Analyzes trend data and identifies patterns]
```

### Troubleshooting
```
You: "List recent calls that had problems"
Claude: [Uses list_calls and filters for issues]

You: "Why are transfers failing?"
Claude: [Analyzes transfer success rates]
```

## ⚡ Quick Reference Commands

### One-Line Analytics
- "KPIs" → Get basic 24h metrics
- "Trends" → Show 7-day call volume 
- "Recent" → List last 20 calls
- "Dashboard" → Full analytics overview

### Department Shortcuts  
- "Sales stats" → Sales department KPIs
- "Support trends" → Support call trends
- "Porting calls" → Recent porting department calls

### Time Shortcuts
- "Today" → 24-hour metrics
- "This week" → 7-day trends  
- "Recent" → Last few calls
- "Now" → Current metrics

## 🎯 Pro Tips for Better Questions

### Be Specific
❌ "Show me stuff"
✅ "Show me sales KPIs for today"

### Use Context
❌ "What about yesterday?"  
✅ "Compare today's call volume to yesterday"

### Ask Follow-ups
✅ First: "Get KPIs"
✅ Then: "Why is the selection rate low?"
✅ Finally: "Show me calls that didn't select anything"

### Chain Questions
✅ "Get trends for sales, then show recent sales calls"
✅ "Compare all departments, then drill into the busiest one"

Remember: Claude can analyze the data it receives, so don't just ask for raw numbers - ask for insights, patterns, and recommendations!