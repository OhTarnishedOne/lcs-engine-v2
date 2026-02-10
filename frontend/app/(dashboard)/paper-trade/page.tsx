import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function PaperTradePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Paper Trade</h1>
        <p className="text-slate-600">Practice trading with simulated money.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Coming Soon</CardTitle>
          <CardDescription>Paper trading will be available in Phase 5.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-slate-600">
            You&apos;ll start with $100,000 in virtual money to practice trading strategies.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
