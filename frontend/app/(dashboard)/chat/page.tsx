import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ChatPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Chat</h1>
        <p className="text-slate-600">Ask questions and learn with your AI tutor.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Coming Soon</CardTitle>
          <CardDescription>Chat interface will be available in Phase 5.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-slate-600">
            Get personalized answers to your investment questions.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
