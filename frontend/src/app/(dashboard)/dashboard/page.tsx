"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Files, MessageSquare, Zap, DollarSign } from "lucide-react";
import { formatCost, formatTokens } from "@/lib/utils";

export default function DashboardPage() {
  // Static data for scaffolding, ideally fetched via React Query + api-client
  const stats = [
    { title: "Total Documents", value: "124", icon: Files, trend: "+12%" },
    { title: "Conversations", value: "892", icon: MessageSquare, trend: "+5.4%" },
    { title: "Tokens Used", value: formatTokens(2450000), icon: Zap, trend: "+14%" },
    { title: "Estimated Cost", value: formatCost(12.45), icon: DollarSign, trend: "+2%" },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-green-500 mt-1">
                {stat.trend} from last month
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Recent Conversations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1,2,3,4].map((i) => (
                <div key={i} className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted transition-colors cursor-pointer">
                  <div className="bg-primary/10 p-2 rounded-full text-primary">
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold">How do I setup SSO?</h4>
                    <p className="text-xs text-muted-foreground">Using model GPT-4o • 2 hours ago</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Recently Uploaded Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1,2,3,4].map((i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors cursor-pointer">
                  <div className="flex items-center gap-3">
                    <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded text-blue-600 dark:text-blue-400">
                      <Files className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium">Q3_Financial_Report.pdf</h4>
                      <p className="text-xs text-muted-foreground">2.4 MB • Processing</p>
                    </div>
                  </div>
                  <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-500">
                    Processing
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
