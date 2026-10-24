"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function HomePage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (loading) return;
    if (user) router.replace("/dashboard");
    else router.replace("/login");
  }, [user, loading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="text-slate-400">Loading...</div>
    </div>
  );
} 