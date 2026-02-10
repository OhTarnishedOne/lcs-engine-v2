import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function StrategiesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Strategies</h1>
        <p className="text-slate-600">Explore AI-generated investment strategies.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Coming Soon</CardTitle>
          <CardDescription>Strategy recommendations will be available in Phase 5.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-slate-600">
            Complete onboarding first to get personalized strategy recommendations.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
