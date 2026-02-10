import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function OnboardingPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Onboarding</CardTitle>
          <CardDescription>
            Complete your profile to get personalized recommendations.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-slate-600">
            Onboarding flow coming in Phase 5...
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
