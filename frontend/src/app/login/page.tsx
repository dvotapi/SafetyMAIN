import { Suspense } from "react";

import { LoadingState } from "@/components/feedback/Feedback";
import { LoginForm } from "@/features/auth/LoginForm";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div style={{ padding: "var(--sm-space-8)" }}>
          <LoadingState label="Загрузка формы входа" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
