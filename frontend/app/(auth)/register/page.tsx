import { Suspense } from "react";
import { RegisterForm } from "@/features/auth/components";

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}
