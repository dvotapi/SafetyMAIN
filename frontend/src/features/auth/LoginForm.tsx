"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";

import { Alert } from "@/components/feedback/Feedback";
import { Button } from "@/components/primitives/Button";
import { Input } from "@/components/primitives/Input";
import { Label } from "@/components/primitives/Label";
import { Heading, Text } from "@/components/primitives/Text";
import { useAuth } from "@/features/auth/AuthProvider";
import { toUserSafeMessage } from "@/services/api/errors";

import styles from "./LoginForm.module.css";

export function LoginForm() {
  const { login, status, error } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const busy = status === "authenticating";

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLocalError(null);
    try {
      await login(email.trim(), password);
      const next = searchParams.get("next");
      router.replace(next && next.startsWith("/") ? next : "/");
    } catch (err) {
      setLocalError(toUserSafeMessage(err));
    }
  }

  const message = localError ?? error;

  return (
    <div className={styles.page}>
      <form className={styles.card} onSubmit={onSubmit} noValidate>
        <Heading level={1}>Sign in</Heading>
        <Text tone="secondary">
          Authenticate to access the SafetyMAIN workspace.
        </Text>
        {message ? (
          <Alert tone="danger" title="Sign-in failed">
            <span role="alert">{message}</span>
          </Alert>
        ) : null}
        <div className={styles.field}>
          <Label htmlFor="login-email" required>
            Email
          </Label>
          <Input
            id="login-email"
            name="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={busy}
          />
        </div>
        <div className={styles.field}>
          <Label htmlFor="login-password" required>
            Password
          </Label>
          <Input
            id="login-password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={busy}
          />
        </div>
        <Button type="submit" loading={busy} disabled={busy}>
          Sign in
        </Button>
      </form>
    </div>
  );
}
