import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Users, Database, AlertCircle } from "lucide-react";

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">System Administration</h2>
        <p className="text-muted-foreground">Global oversight for all workspaces and system health.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex justify-between">
              Total Users <Users size={16} />
            </CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">1,245</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex justify-between">
              Workspaces <Activity size={16} />
            </CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">84</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex justify-between">
              Vector DB Size <Database size={16} />
            </CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">42.5 GB</div></CardContent>
        </Card>
        <Card className="bg-red-50 dark:bg-red-900/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-red-600 flex justify-between">
              System Errors (24h) <AlertCircle size={16} />
            </CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-600">3</div></CardContent>
        </Card>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>System Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-black text-green-400 p-4 rounded-md font-mono text-sm h-[300px] overflow-y-auto">
            <div>[INFO] 2024-02-15 10:23:41 - Vector reindexing completed for WS-124</div>
            <div>[INFO] 2024-02-15 10:25:12 - New user sign up: user@example.com</div>
            <div className="text-yellow-400">[WARN] 2024-02-15 10:26:05 - API rate limit approaching for OpenAI integration</div>
            <div>[INFO] 2024-02-15 10:30:00 - Routine backup initiated.</div>
            <div className="text-red-400">[ERROR] 2024-02-15 10:31:12 - Failed to parse PDF document ID 4921</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
