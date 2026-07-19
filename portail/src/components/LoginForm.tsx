"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { loginAction, type LoginState } from "@/actions/auth";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="min-h-touch w-full rounded-xl bg-brand text-base font-semibold text-white transition active:scale-[0.99] disabled:opacity-60"
    >
      {pending ? "Connexion…" : "Connexion"}
    </button>
  );
}

export function LoginForm() {
  const [state, formAction] = useActionState<LoginState, FormData>(loginAction, {});

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1">
        <span className="text-sm font-medium text-slate-700">Identifiant</span>
        <input
          name="usr"
          type="text"
          autoComplete="username"
          autoCapitalize="none"
          autoCorrect="off"
          required
          className="min-h-touch rounded-xl border border-slate-300 px-4 outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
          placeholder="email ou nom d'utilisateur"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-sm font-medium text-slate-700">Mot de passe</span>
        <input
          name="pwd"
          type="password"
          autoComplete="current-password"
          required
          className="min-h-touch rounded-xl border border-slate-300 px-4 outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
          placeholder="••••••••"
        />
      </label>

      {state.error ? (
        <p
          role="alert"
          className="rounded-lg bg-red-50 px-3 py-2 text-sm font-medium text-red-700"
        >
          {state.error}
        </p>
      ) : null}

      <SubmitButton />
    </form>
  );
}
