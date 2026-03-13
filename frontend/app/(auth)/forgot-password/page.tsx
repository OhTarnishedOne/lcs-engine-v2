"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Lock, Mail } from "lucide-react";

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
import { api } from "@/lib/api/client";

const forgotSchema = z.object({
  email: z.string().email("Please enter a valid email"),
});

type ForgotFormValues = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<ForgotFormValues>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: "" },
  });

  async function onSubmit(data: ForgotFormValues) {
    setIsLoading(true);
    setError(null);

    try {
      await api.forgotPassword(data.email);
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-lg border-gray-700 bg-[#111827] text-white shadow-xl">
      <CardHeader className="space-y-2 px-10 pt-10 pb-6">
        <CardTitle className="text-2xl font-bold text-white">
          Reset your password
        </CardTitle>
        <p className="text-base text-gray-400">
          {submitted
            ? "Check your email"
            : "Enter your email and we'll send you a reset link"}
        </p>
      </CardHeader>

      {submitted ? (
        <>
          <CardContent className="px-10">
            <div className="rounded-lg bg-[#00D4AA]/10 border border-[#00D4AA]/20 p-4">
              <div className="flex items-start gap-3">
                <Mail className="mt-0.5 h-5 w-5 text-[#00D4AA] shrink-0" />
                <p className="text-sm text-gray-300">
                  If an account exists with that email address, we&apos;ve sent
                  a password reset link. Check your inbox and spam folder.
                </p>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4 px-10 pb-10 pt-4">
            <Link href="/login" className="w-full">
              <Button
                variant="outline"
                className="h-12 w-full text-base font-semibold border-gray-700 bg-transparent text-white hover:bg-[#1A2942]"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to login
              </Button>
            </Link>
          </CardFooter>
        </>
      ) : (
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
            </CardContent>
            <CardFooter className="flex flex-col space-y-4 px-10 pb-10 pt-2">
              <Button
                type="submit"
                className="h-12 w-full text-base font-semibold bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] hover:-translate-y-0.5 transition-all"
                disabled={isLoading}
              >
                {isLoading ? "Sending..." : "Send reset link"}
              </Button>
              <p className="text-center text-sm text-gray-400">
                Remember your password?{" "}
                <Link
                  href="/login"
                  className="font-medium text-[#00D4AA] hover:underline underline-offset-2"
                >
                  Sign in
                </Link>
              </p>
              <div className="flex w-full items-center gap-3 pt-2">
                <div className="h-px flex-1 bg-gray-700" />
                <div className="h-px flex-1 bg-gray-700" />
              </div>
              <div className="flex items-center justify-center gap-1.5 text-xs text-gray-500">
                <Lock className="h-3 w-3" />
                <span>
                  Secure authentication &middot; Your data stays private
                </span>
              </div>
            </CardFooter>
          </form>
        </Form>
      )}
    </Card>
  );
}
