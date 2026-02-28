"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Lock } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useAuthStore } from "@/stores/auth-store";
import { trackEvent } from "@/lib/analytics";

const registerSchema = z
  .object({
    email: z.string().email("Please enter a valid email"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])|(?=.*\d)/,
        "Password must contain at least one letter and one number"
      ),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const router = useRouter();
  const register = useAuthStore((state) => state.register);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  async function onSubmit(data: RegisterFormValues) {
    setIsLoading(true);
    setError(null);

    try {
      await register({ email: data.email, password: data.password });
      trackEvent("signup_completed");
      router.push("/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-lg border-gray-700 bg-[#111827] text-white shadow-xl">
      <CardHeader className="space-y-2 px-10 pt-10 pb-6">
        <CardTitle className="text-2xl font-bold text-white">
          Create your account
        </CardTitle>
        <p className="text-base text-gray-400">
          Enter your email and create a password to get started for free
        </p>
      </CardHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardContent className="space-y-5 px-10">
            {error && (
              <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
                {error}
              </div>
            )}
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base text-gray-300">
                    Email
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="you@example.com"
                      autoComplete="email"
                      className="h-12 text-base rounded-lg border-gray-700 bg-[#1A2942] text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:ring-[#00D4AA]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base text-gray-300">
                    Password
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder="Create a password"
                      autoComplete="new-password"
                      className="h-12 text-base rounded-lg border-gray-700 bg-[#1A2942] text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:ring-[#00D4AA]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="confirmPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base text-gray-300">
                    Confirm Password
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder="Confirm your password"
                      autoComplete="new-password"
                      className="h-12 text-base rounded-lg border-gray-700 bg-[#1A2942] text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:ring-[#00D4AA]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
          <CardFooter className="flex flex-col space-y-4 px-10 pb-10 pt-2">
            <Button
              type="submit"
              className="h-12 w-full text-base font-semibold bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] hover:-translate-y-0.5 transition-all"
              disabled={isLoading}
            >
              {isLoading ? "Creating account..." : "Create A Free Account"}
            </Button>
            <p className="text-center text-sm text-gray-400">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-medium text-[#00D4AA] hover:underline underline-offset-2"
              >
                Sign in
              </Link>
            </p>

            {/* Divider */}
            <div className="flex w-full items-center gap-3 pt-2">
              <div className="h-px flex-1 bg-gray-700" />
              <div className="h-px flex-1 bg-gray-700" />
            </div>

            {/* Trust signal */}
            <div className="flex items-center justify-center gap-1.5 text-xs text-gray-500">
              <Lock className="h-3 w-3" />
              <span>Secure authentication &middot; Your data stays private</span>
            </div>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}
