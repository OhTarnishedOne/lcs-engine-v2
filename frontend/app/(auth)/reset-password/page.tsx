"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CheckCircle, Eye, EyeOff, Lock } from "lucide-react";

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

const resetSchema = z
  .object({
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

type ResetFormValues = z.infer<typeof resetSchema>;

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordContent />
    </Suspense>
  );
}

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const form = useForm<ResetFormValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { password: "", confirmPassword: "" },
  });

  async function onSubmit(data: ResetFormValues) {
    if (!token) return;

    setIsLoading(true);
    setError(null);

    try {
      await api.resetPassword(token, data.password);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  }

  // No token in URL
  if (!token) {
    return (
      <Card className="w-full max-w-lg border-gray-700 bg-[#111827] text-white shadow-xl">
        <CardHeader className="space-y-2 px-10 pt-10 pb-6">
          <CardTitle className="text-2xl font-bold text-white">
            Invalid reset link
          </CardTitle>
          <p className="text-base text-gray-400">
            This password reset link is invalid or missing a token.
          </p>
        </CardHeader>
        <CardFooter className="px-10 pb-10 pt-2">
          <Link href="/forgot-password" className="w-full">
            <Button className="h-12 w-full text-base font-semibold bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]">
              Request a new reset link
            </Button>
          </Link>
        </CardFooter>
      </Card>
    );
  }

  // Success state
  if (success) {
    return (
      <Card className="w-full max-w-lg border-gray-700 bg-[#111827] text-white shadow-xl">
        <CardHeader className="space-y-2 px-10 pt-10 pb-6">
          <CardTitle className="text-2xl font-bold text-white">
            Password reset successfully
          </CardTitle>
        </CardHeader>
        <CardContent className="px-10">
          <div className="rounded-lg bg-[#00D4AA]/10 border border-[#00D4AA]/20 p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="mt-0.5 h-5 w-5 text-[#00D4AA] shrink-0" />
              <p className="text-sm text-gray-300">
                Your password has been updated. You can now sign in with your
                new password.
              </p>
            </div>
          </div>
        </CardContent>
        <CardFooter className="px-10 pb-10 pt-4">
          <Link href="/login" className="w-full">
            <Button className="h-12 w-full text-base font-semibold bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] hover:-translate-y-0.5 transition-all">
              Sign in
            </Button>
          </Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-lg border-gray-700 bg-[#111827] text-white shadow-xl">
      <CardHeader className="space-y-2 px-10 pt-10 pb-6">
        <CardTitle className="text-2xl font-bold text-white">
          Create new password
        </CardTitle>
        <p className="text-base text-gray-400">
          Enter your new password below
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
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-base text-gray-300">
                    New Password
                  </FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input
                        type={showPassword ? "text" : "password"}
                        placeholder="Create a new password"
                        autoComplete="new-password"
                        className="h-12 text-base rounded-lg border-gray-700 bg-[#1A2942] text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:ring-[#00D4AA] pr-11"
                        {...field}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
                        tabIndex={-1}
                      >
                        {showPassword ? (
                          <EyeOff className="h-5 w-5" />
                        ) : (
                          <Eye className="h-5 w-5" />
                        )}
                      </button>
                    </div>
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
                    <div className="relative">
                      <Input
                        type={showConfirmPassword ? "text" : "password"}
                        placeholder="Confirm your new password"
                        autoComplete="new-password"
                        className="h-12 text-base rounded-lg border-gray-700 bg-[#1A2942] text-white placeholder:text-gray-500 focus:border-[#00D4AA] focus:ring-[#00D4AA] pr-11"
                        {...field}
                      />
                      <button
                        type="button"
                        onClick={() =>
                          setShowConfirmPassword(!showConfirmPassword)
                        }
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
                        tabIndex={-1}
                      >
                        {showConfirmPassword ? (
                          <EyeOff className="h-5 w-5" />
                        ) : (
                          <Eye className="h-5 w-5" />
                        )}
                      </button>
                    </div>
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
              {isLoading ? "Resetting..." : "Reset password"}
            </Button>
            <p className="text-center text-sm text-gray-400">
              <Link
                href="/forgot-password"
                className="font-medium text-[#00D4AA] hover:underline underline-offset-2"
              >
                Request a new reset link
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
    </Card>
  );
}
