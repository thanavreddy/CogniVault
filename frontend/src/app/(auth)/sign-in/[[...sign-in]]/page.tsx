import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-white dark:from-slate-900 dark:to-slate-800">
      <div className="absolute top-8 left-8">
        <h1 className="text-2xl font-bold text-primary">KnowledgeAI</h1>
      </div>
      <div className="animate-slide-up">
        <SignIn 
          appearance={{
            elements: {
              formButtonPrimary: 
                "bg-primary hover:bg-primary/90 text-primary-foreground",
              card: "shadow-xl border border-border bg-card",
            }
          }}
        />
      </div>
    </div>
  );
}
