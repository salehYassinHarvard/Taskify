"use client";

import { BookOpenCheck, Loader2, TriangleAlert } from "lucide-react";
import { useState } from "react";

import { TrafficLights } from "@/components/TrafficLights";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const supabase = createClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function signIn() {
    setLoading(true);
    setError(null);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        scopes: "openid email profile https://www.googleapis.com/auth/calendar",
      },
    });
    if (error) {
      setError(error.message);
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="flex flex-col items-center gap-4 py-12">
        <div
          className="w-[84px] h-[84px] rounded-[20px] flex items-center justify-center mb-2"
          style={{
            background: "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)",
            boxShadow:
              "0 16px 40px rgba(59,130,246,0.35), 0 1px 0 rgba(255,255,255,0.20) inset",
          }}
        >
          <BookOpenCheck className="w-10 h-10 text-white" />
        </div>

        <h1 className="text-4xl font-bold text-center tracking-tightest">
          Welcome to Taskify
        </h1>
        <p className="text-zinc-400 text-center max-w-sm tracking-tight">
          Your assignments, calendar, and syllabi — together at last.
        </p>

        <div className="mac-glass mac-anim rounded-macLg w-[400px] overflow-hidden mt-2">
          <div className="flex items-center px-3 py-3 border-b border-white/5">
            <TrafficLights />
            <div className="flex-1 text-center text-[11px] text-zinc-400 font-medium">
              Sign in
            </div>
            <div className="w-[38px]" />
          </div>

          <div className="p-6 space-y-3 flex flex-col items-center">
            <div className="text-center">
              <div className="font-medium tracking-tight">
                Sign in to get started
              </div>
              <div className="text-[12px] text-zinc-400 mt-1">
                Use your Google account — same one you use for school.
              </div>
            </div>

            <button
              onClick={signIn}
              disabled={loading}
              className="mac-button w-full py-2.5"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <GoogleIcon />
              )}
              Continue with Google
            </button>

            {error && (
              <div className="w-full flex items-start gap-2 rounded-lg bg-red-500/10 ring-1 ring-red-400/20 p-3 text-[12px] text-red-300">
                <TriangleAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
                {error}
              </div>
            )}
          </div>
        </div>

        <p className="text-[11px] text-zinc-500 mt-2">
          By signing in you agree to our Terms of Service.
        </p>
      </div>
    </main>
  );
}

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-4 h-4" aria-hidden>
      <path
        fill="#fff"
        d="M21.35 11.1H12v2.94h5.34c-.23 1.5-1.71 4.4-5.34 4.4-3.21 0-5.83-2.66-5.83-5.94S8.79 6.56 12 6.56c1.83 0 3.05.78 3.75 1.45l2.55-2.45C16.79 4.06 14.62 3 12 3 6.95 3 2.86 7.04 2.86 12s4.09 9 9.14 9c5.27 0 8.77-3.7 8.77-8.91 0-.6-.07-1.05-.16-1.49z"
      />
    </svg>
  );
}
