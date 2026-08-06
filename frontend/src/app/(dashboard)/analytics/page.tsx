"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const usageData = [
  { name: 'Mon', tokens: 4000, cost: 0.12 },
  { name: 'Tue', tokens: 3000, cost: 0.09 },
  { name: 'Wed', tokens: 2000, cost: 0.06 },
  { name: 'Thu', tokens: 2780, cost: 0.08 },
  { name: 'Fri', tokens: 1890, cost: 0.05 },
  { name: 'Sat', tokens: 2390, cost: 0.07 },
  { name: 'Sun', tokens: 3490, cost: 0.10 },
];

const modelData = [
  { name: 'GPT-4o', value: 400 },
  { name: 'Claude 3.5 Sonnet', value: 300 },
  { name: 'Llama 3 70B', value: 300 },
];
const COLORS = ['#3b82f6', '#10b981', '#f59e0b'];

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Analytics</h2>
        <p className="text-muted-foreground">Monitor your AI Assistant's performance and cost.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Token Usage (Last 7 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={usageData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#88888833" />
                  <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value / 1000}k`} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: '1px solid var(--border)', backgroundColor: 'var(--card)', color: 'var(--card-foreground)' }} 
                  />
                  <Line type="monotone" dataKey="tokens" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Model Usage Distribution</CardTitle>
          </CardHeader>
          <CardContent className="flex justify-center items-center h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={modelData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  fill="#8884d8"
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {modelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Most Common Queries</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { query: "How to configure SSO via SAML?", count: 145 },
              { query: "Q3 financial highlights", count: 89 },
              { query: "Employee remote work policy 2024", count: 67 },
              { query: "System architecture overview", count: 42 },
            ].map((item, i) => (
              <div key={i} className="flex justify-between items-center py-2 border-b last:border-0">
                <span className="text-sm">{item.query}</span>
                <span className="text-sm text-muted-foreground font-mono">{item.count} req</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
