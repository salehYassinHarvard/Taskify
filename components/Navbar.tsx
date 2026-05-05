"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BookOpenCheck, LogOut, Settings as SettingsIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { TrafficLights } from "./TrafficLights";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const supabase = createClient();
  const [user, setUser] = useState<{
    email: string;
    name: string;
    avatar: string;
  } | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) {
        setUser({
          email: user.email ?? "",
          name:
            (user.user_metadata?.full_name as string) ??
            (user.user_metadata?.name as string) ??
            "",
          avatar: (user.user_metadata?.avatar_url as string) ?? "",
        });
      }
    });
  }, [supabase]);

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  const NavLink = ({ href, label }: { href: string; label: string }) => {
    const active = pathname === href;
    return (
      <Link
        href={href}
        className={cn(
          "px-3 py-1.5 rounded-lg text-[13px] font-medium transition-colors",
          active
            ? "bg-white/10 text-white dark:text-white"
            : "text-zinc-300 hover:bg-white/5 hover:text-white",
          "dark:text-zinc-300",
          // light overrides
          "[html:not(.dark)_&]:text-zinc-700",
          active &&
            "[html:not(.dark)_&]:bg-black/5 [html:not(.dark)_&]:text-zinc-900",
        )}
      >
        {label}
      </Link>
    );
  };

  return (
    <header className="mac-titlebar">
      <div className="mx-auto max-w-7xl flex items-center gap-4 px-5 py-2.5">
        <TrafficLights />
        <Link href="/dashboard" className="flex items-center gap-2 ml-2">
          <BookOpenCheck className="w-[18px] h-[18px] text-blue-400" />
          <span className="font-bold text-[15px] tracking-tighter">
            Taskify
          </span>
        </Link>

        <div className="flex-1" />

        <nav className="flex items-center gap-1">
          <NavLink href="/dashboard" label="Dashboard" />
          <NavLink href="/settings" label="Settings" />
        </nav>

        <div className="flex-1" />

        <div className="relative">
          <button
            onClick={() => setMenuOpen((s) => !s)}
            className="rounded-full overflow-hidden w-8 h-8 ring-1 ring-white/10 hover:ring-white/20 transition"
            aria-label="User menu"
          >
            {user?.avatar ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={user.avatar}
                alt={user.name || user.email || "User"}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-zinc-700 text-white text-xs font-semibold">
                {(user?.email?.[0] ?? "?").toUpperCase()}
              </div>
            )}
          </button>

          {menuOpen && user && (
            <>
              <button
                className="fixed inset-0 z-40 cursor-default"
                onClick={() => setMenuOpen(false)}
                aria-label="Close menu"
              />
              <div className="absolute right-0 mt-2 w-64 rounded-mac mac-glass z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-white/5">
                  <div className="font-medium text-sm truncate">
                    {user.name || user.email}
                  </div>
                  <div className="text-xs text-zinc-400 truncate">
                    {user.email}
                  </div>
                </div>
                <Link
                  href="/settings"
                  className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-white/5"
                  onClick={() => setMenuOpen(false)}
                >
                  <SettingsIcon className="w-4 h-4" /> Settings
                </Link>
                <button
                  onClick={handleSignOut}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 text-left"
                >
                  <LogOut className="w-4 h-4" /> Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
