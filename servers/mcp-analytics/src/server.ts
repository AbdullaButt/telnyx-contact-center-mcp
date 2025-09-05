#!/usr/bin/env node
/**
 * MCP Analytics Server for Telnyx Contact Center
 * Exposes call analytics and KPIs via MCP protocol
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import Database from "better-sqlite3";
import * as path from "path";

// Database configuration
const DB_PATH = process.env.ANALYTICS_DB || path.join("..", "..", "analytics.sqlite");

interface KPIResult {
  window: string;
  department: string;
  inbound_volume: number;
  selection_rate: number;
  transfer_success: number;
}

interface TrendResult {
  day: string;
  calls: number;
}

interface RecentCallResult {
  call_control_id: string;
  department: string | null;
  digit: string | null;
  ts: string;
}

class AnalyticsServer {
  private server: Server;
  private db!: Database.Database;

  constructor() {
    this.server = new Server(
      {
        name: "mcp-analytics",
        version: "0.1.0",
      },
      {
        capabilities: {
          resources: {},
          tools: {},
        },
      }
    );

    this.setupErrorHandling();
    this.setupHandlers();
    this.initializeDatabase();
  }

  private initializeDatabase(): void {
    try {
      this.db = new Database(DB_PATH, { readonly: true });
      console.error(`MCP Analytics Server connected to database: ${DB_PATH}`);
    } catch (error) {
      console.error(`Failed to connect to database ${DB_PATH}:`, error);
      process.exit(1);
    }
  }

  private setupErrorHandling(): void {
    this.server.onerror = (error) => console.error("[MCP Error]", error);
    process.on("SIGINT", async () => {
      await this.server.close();
      this.db?.close();
      process.exit(0);
    });
  }

  private setupHandlers(): void {
    this.setupToolHandlers();
    this.setupResourceHandlers();
  }

  private setupToolHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "get_kpis",
          description: "Get 24-hour KPIs (inbound volume, selection rate, transfer success)",
          inputSchema: {
            type: "object",
            properties: {
              department: {
                type: "string",
                enum: ["sales", "support", "porting"],
                description: "Filter by department (optional)",
              },
            },
          },
        },
        {
          name: "get_trend",
          description: "Get daily call volume trend",
          inputSchema: {
            type: "object",
            properties: {
              days: {
                type: "number",
                minimum: 1,
                maximum: 365,
                default: 7,
                description: "Number of days to include in trend",
              },
              department: {
                type: "string",
                enum: ["sales", "support", "porting"],
                description: "Filter by department (optional)",
              },
            },
          },
        },
        {
          name: "list_calls",
          description: "List recent calls with IVR selections",
          inputSchema: {
            type: "object",
            properties: {
              limit: {
                type: "number",
                minimum: 1,
                maximum: 1000,
                default: 20,
                description: "Maximum number of calls to return",
              },
              department: {
                type: "string",
                enum: ["sales", "support", "porting"],
                description: "Filter by department (optional)",
              },
            },
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "get_kpis":
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(await this.getKPIs(args?.department as string | undefined), null, 2),
                },
              ],
            };

          case "get_trend":
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(await this.getTrend((args?.days as number) || 7, args?.department as string | undefined), null, 2),
                },
              ],
            };

          case "list_calls":
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(await this.getRecentCalls((args?.limit as number) || 20, args?.department as string | undefined), null, 2),
                },
              ],
            };

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  private setupResourceHandlers(): void {
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
      resources: [
        {
          uri: "analytics://dashboard_24h",
          name: "24-hour Analytics Dashboard",
          description: "JSON snapshot of KPIs for all departments",
          mimeType: "application/json",
        },
      ],
    }));

    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;

      if (uri === "analytics://dashboard_24h") {
        try {
          const dashboard = await this.getDashboard24h();
          return {
            contents: [
              {
                uri,
                mimeType: "application/json",
                text: JSON.stringify(dashboard, null, 2),
              },
            ],
          };
        } catch (error) {
          throw new Error(`Failed to generate dashboard: ${error instanceof Error ? error.message : String(error)}`);
        }
      }

      throw new Error(`Unknown resource: ${uri}`);
    });
  }

  private async getKPIs(department?: string): Promise<KPIResult> {
    // Calculate 24h window
    const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    
    try {
      // Inbound volume
      let volumeQuery = `
        SELECT COUNT(DISTINCT c.call_control_id) as volume
        FROM calls c
        LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
        WHERE c.created_at >= ?
      `;
      const volumeParams = [cutoff];

      if (department) {
        volumeQuery += ` AND ivr.department = ?`;
        volumeParams.push(department);
      }

      const volumeResult = this.db.prepare(volumeQuery).get(...volumeParams) as { volume: number };
      const inbound_volume = volumeResult?.volume || 0;

      // Selection rate
      let selectionQuery: string;
      let selectionParams: string[];

      if (department) {
        selectionQuery = `
          SELECT 
            COUNT(DISTINCT ivr.call_control_id) as with_selection,
            (SELECT COUNT(DISTINCT c2.call_control_id) 
             FROM calls c2 
             LEFT JOIN ivr_interactions ivr2 ON c2.call_control_id = ivr2.call_control_id
             WHERE c2.created_at >= ? AND ivr2.department = ?) as total_calls
          FROM ivr_interactions ivr
          JOIN calls c ON ivr.call_control_id = c.call_control_id
          WHERE c.created_at >= ? AND ivr.department = ?
        `;
        selectionParams = [cutoff, department, cutoff, department];
      } else {
        selectionQuery = `
          SELECT 
            COUNT(DISTINCT ivr.call_control_id) as with_selection,
            COUNT(DISTINCT c.call_control_id) as total_calls
          FROM calls c
          LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
          WHERE c.created_at >= ?
        `;
        selectionParams = [cutoff];
      }

      const selectionResult = this.db.prepare(selectionQuery).get(...selectionParams) as { with_selection: number; total_calls: number };
      const selection_rate = selectionResult?.total_calls > 0 
        ? selectionResult.with_selection / selectionResult.total_calls 
        : 0.0;

      // Transfer success rate
      let transferQuery: string;
      let transferParams: string[];

      if (department) {
        transferQuery = `
          SELECT 
            COUNT(CASE WHEN t.status = 'success' THEN 1 END) as successful,
            COUNT(*) as total_transfers
          FROM transfers t
          JOIN calls c ON t.call_control_id = c.call_control_id
          JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
          WHERE c.created_at >= ? AND ivr.department = ?
        `;
        transferParams = [cutoff, department];
      } else {
        transferQuery = `
          SELECT 
            COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
            COUNT(*) as total_transfers
          FROM transfers t
          JOIN calls c ON t.call_control_id = c.call_control_id
          WHERE c.created_at >= ?
        `;
        transferParams = [cutoff];
      }

      const transferResult = this.db.prepare(transferQuery).get(...transferParams) as { successful: number; total_transfers: number };
      const transfer_success = transferResult?.total_transfers > 0 
        ? transferResult.successful / transferResult.total_transfers 
        : 0.0;

      return {
        window: "24h",
        department: department || "all",
        inbound_volume,
        selection_rate: Math.round(selection_rate * 1000) / 1000,
        transfer_success: Math.round(transfer_success * 1000) / 1000,
      };

    } catch (error) {
      console.error("Error getting KPIs:", error);
      return {
        window: "24h",
        department: department || "all",
        inbound_volume: 0,
        selection_rate: 0.0,
        transfer_success: 0.0,
      };
    }
  }

  private async getTrend(days: number, department?: string): Promise<{ days: number; department: string; trend: TrendResult[] }> {
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();
    
    try {
      let query: string;
      let params: string[];

      if (department) {
        query = `
          SELECT 
            DATE(c.created_at) as day,
            COUNT(DISTINCT c.call_control_id) as calls
          FROM calls c
          LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
          WHERE c.created_at >= ? AND (ivr.department = ? OR ivr.department IS NULL)
          GROUP BY DATE(c.created_at)
          ORDER BY day DESC
        `;
        params = [cutoff, department];
      } else {
        query = `
          SELECT 
            DATE(created_at) as day,
            COUNT(*) as calls
          FROM calls
          WHERE created_at >= ?
          GROUP BY DATE(created_at)
          ORDER BY day DESC
        `;
        params = [cutoff];
      }

      const results = this.db.prepare(query).all(...params) as TrendResult[];

      return {
        days,
        department: department || "all",
        trend: results,
      };

    } catch (error) {
      console.error("Error getting trend:", error);
      return {
        days,
        department: department || "all",
        trend: [],
      };
    }
  }

  private async getRecentCalls(limit: number, department?: string): Promise<{ limit: number; department: string; calls: RecentCallResult[] }> {
    try {
      let query: string;
      let params: (string | number)[];

      if (department) {
        query = `
          SELECT 
            c.call_control_id,
            ivr.department,
            ivr.digit,
            c.created_at as ts
          FROM calls c
          LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
          WHERE ivr.department = ?
          ORDER BY c.created_at DESC
          LIMIT ?
        `;
        params = [department, limit];
      } else {
        query = `
          SELECT 
            c.call_control_id,
            ivr.department,
            ivr.digit,
            c.created_at as ts
          FROM calls c
          LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
          ORDER BY c.created_at DESC
          LIMIT ?
        `;
        params = [limit];
      }

      const results = this.db.prepare(query).all(...params) as RecentCallResult[];

      return {
        limit,
        department: department || "all",
        calls: results,
      };

    } catch (error) {
      console.error("Error getting recent calls:", error);
      return {
        limit,
        department: department || "all",
        calls: [],
      };
    }
  }

  private async getDashboard24h(): Promise<Record<string, KPIResult>> {
    const departments = ["sales", "support", "porting"];
    const dashboard: Record<string, KPIResult> = {};

    // Get KPIs for all departments
    dashboard.all = await this.getKPIs();

    // Get KPIs for each specific department
    for (const dept of departments) {
      dashboard[dept] = await this.getKPIs(dept);
    }

    return dashboard;
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("MCP Analytics Server started successfully");
  }
}

const server = new AnalyticsServer();
server.run().catch(console.error);