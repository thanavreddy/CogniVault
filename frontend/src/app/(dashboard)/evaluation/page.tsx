"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ShieldAlert, CheckCircle, AlertTriangle } from "lucide-react";

export default function EvaluationPage() {
  const metrics = [
    { name: "Faithfulness", score: 94, description: "Answers directly supported by retrieved context" },
    { name: "Relevance", score: 88, description: "Answers directly address user query" },
    { name: "Groundedness", score: 91, description: "Factual correctness based on documents" },
    { name: "Coherence", score: 96, description: "Logical flow and structure of response" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">System Evaluation</h2>
          <p className="text-muted-foreground">Automated RAG evaluation metrics (RAGAS framework).</p>
        </div>
        <div className="flex items-center gap-2 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 px-3 py-1.5 rounded-full text-sm font-medium">
          <CheckCircle size={16} />
          <span>System Healthy</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m) => (
          <Card key={m.name}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{m.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-2">{m.score}%</div>
              <Progress value={m.score} className="h-2 mb-2" />
              <p className="text-xs text-muted-foreground">{m.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Flagged Responses</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="border rounded-lg p-4 bg-red-50 dark:bg-red-900/10">
              <div className="flex gap-2 items-center mb-2 text-red-600 dark:text-red-400">
                <ShieldAlert size={16} />
                <span className="font-semibold text-sm">Potential Hallucination Detected</span>
              </div>
              <p className="text-sm mb-2 font-medium">Query: Who is the CEO of Acme Corp?</p>
              <p className="text-sm text-muted-foreground italic mb-2">
                Response: The CEO of Acme Corp is John Smith.
              </p>
              <p className="text-xs text-destructive">
                Reason: "John Smith" was not found in any retrieved documents context.
              </p>
            </div>
            
            <div className="border rounded-lg p-4 bg-yellow-50 dark:bg-yellow-900/10">
              <div className="flex gap-2 items-center mb-2 text-yellow-600 dark:text-yellow-400">
                <AlertTriangle size={16} />
                <span className="font-semibold text-sm">Low Relevance Score (45%)</span>
              </div>
              <p className="text-sm mb-2 font-medium">Query: Setup local dev environment</p>
              <p className="text-sm text-muted-foreground italic mb-2">
                Response: The production environment uses AWS EKS...
              </p>
              <p className="text-xs text-yellow-700 dark:text-yellow-500">
                Reason: Response discusses production instead of local development.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
