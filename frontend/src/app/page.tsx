import Link from "next/link";
import { ArrowRight, Brain, Database, Shield, Zap } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="px-6 py-4 flex justify-between items-center border-b">
        <div className="flex items-center gap-2">
          <Brain className="w-8 h-8 text-primary" />
          <span className="text-xl font-bold">KnowledgeAI</span>
        </div>
        <div className="flex gap-4 items-center">
          <Link href="/sign-in" className="text-sm font-medium hover:text-primary transition-colors">
            Sign In
          </Link>
          <Link 
            href="/sign-up" 
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </header>

      <main className="flex-1">
        <section className="py-20 px-6 text-center max-w-5xl mx-auto flex flex-col items-center justify-center min-h-[70vh]">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 bg-clip-text text-transparent bg-gradient-to-r from-primary to-indigo-400">
            Enterprise AI Knowledge Assistant
          </h1>
          <p className="text-xl text-muted-foreground mb-10 max-w-2xl">
            Securely connect your organization's data with advanced LLMs. 
            Experience zero-hallucination RAG, multi-agent workflows, and robust evaluation.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link 
              href="/sign-up" 
              className="flex items-center gap-2 bg-primary text-primary-foreground px-8 py-4 rounded-lg text-lg font-medium hover:bg-primary/90 transition-all shadow-lg hover:shadow-xl"
            >
              Start Free Trial <ArrowRight className="w-5 h-5" />
            </Link>
            <Link 
              href="#features" 
              className="flex items-center gap-2 bg-secondary text-secondary-foreground px-8 py-4 rounded-lg text-lg font-medium hover:bg-secondary/80 transition-all"
            >
              View Features
            </Link>
          </div>
        </section>

        <section id="features" className="py-20 bg-muted/50 px-6">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">Enterprise-Grade Architecture</h2>
            <div className="grid md:grid-cols-3 gap-8">
              <FeatureCard 
                icon={<Database className="w-10 h-10 text-primary mb-4" />}
                title="Advanced RAG"
                description="Hybrid search (vector + keyword) with automatic chunking, metadata extraction, and re-ranking for highest relevance."
              />
              <FeatureCard 
                icon={<Shield className="w-10 h-10 text-primary mb-4" />}
                title="Data Privacy & Security"
                description="Your data never trains public models. Role-based access control, SOC2 compliance ready, and audit logging."
              />
              <FeatureCard 
                icon={<Zap className="w-10 h-10 text-primary mb-4" />}
                title="Continuous Evaluation"
                description="Automated metrics for faithfulness, relevance, and groundedness. Monitor and improve system accuracy over time."
              />
            </div>
          </div>
        </section>
      </main>

      <footer className="py-8 border-t text-center text-muted-foreground text-sm">
        <p>&copy; {new Date().getFullYear()} KnowledgeAI. All rights reserved.</p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="bg-card text-card-foreground p-8 rounded-xl border shadow-sm hover:shadow-md transition-shadow">
      {icon}
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </div>
  );
}
