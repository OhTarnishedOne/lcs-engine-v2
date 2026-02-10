import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ProbabilityLabPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Probability Lab</h1>
        <p className="text-slate-600">Improve your forecasting skills with real-world predictions.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Coming Soon</CardTitle>
          <CardDescription>Probability Lab will be available in Phase 5.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-slate-600">
            Make predictions on real-world events and track your calibration score.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
