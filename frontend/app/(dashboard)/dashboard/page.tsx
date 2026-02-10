import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  GraduationCap,
  BarChart3,
  LineChart,
  MessageSquare,
} from "lucide-react";

const features = [
  {
    title: "Onboarding",
    description: "Complete your profile to get personalized recommendations",
    icon: GraduationCap,
    href: "/onboarding",
    color: "text-blue-600",
    bgColor: "bg-blue-50",
  },
  {
    title: "Strategies",
    description: "Explore AI-generated investment strategies",
    icon: BarChart3,
    href: "/strategies",
    color: "text-emerald-600",
    bgColor: "bg-emerald-50",
  },
  {
    title: "Paper Trade",
    description: "Practice trading with simulated money",
    icon: LineChart,
    href: "/paper-trade",
    color: "text-amber-600",
    bgColor: "bg-amber-50",
  },
  {
    title: "Chat",
    description: "Ask questions and learn with your AI tutor",
    icon: MessageSquare,
    href: "/chat",
    color: "text-purple-600",
    bgColor: "bg-purple-50",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">
          Welcome to LCS Engine
        </h1>
        <p className="mt-2 text-slate-600">
          Your personalized investment learning platform. Get started by
          exploring the features below.
        </p>
      </div>

      {/* Feature Cards */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {features.map((feature) => (
          <Card key={feature.title} className="relative overflow-hidden">
            <CardHeader>
              <div
                className={`inline-flex h-12 w-12 items-center justify-center rounded-lg ${feature.bgColor}`}
              >
                <feature.icon className={`h-6 w-6 ${feature.color}`} />
              </div>
              <CardTitle className="mt-4">{feature.title}</CardTitle>
              <CardDescription>{feature.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" className="w-full">
                <Link href={feature.href}>Get Started</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Stats - Placeholder */}
      <div className="grid gap-6 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Learning Progress</CardDescription>
            <CardTitle className="text-3xl">0%</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Complete onboarding to start tracking
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Paper Trading Balance</CardDescription>
            <CardTitle className="text-3xl">$100,000</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Starting balance for practice
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Chat Conversations</CardDescription>
            <CardTitle className="text-3xl">0</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Start chatting with your AI tutor
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
