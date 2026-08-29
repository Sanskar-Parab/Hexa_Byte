"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Logo } from "@/components/layout/Logo";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const { login, loadDemo } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form.email, form.password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setLoading(true);
    try {
      await loadDemo();
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Demo load failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas-soft px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 flex justify-center">
          <Link href="/">
            <Logo size="lg" />
          </Link>
        </div>

        <Card className="shadow-panel">
          <CardHeader className="text-center">
            <CardTitle className="text-xl">Welcome back</CardTitle>
            <CardDescription>Sign in to continue toward your next move.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-lg bg-err-soft p-3 text-sm text-err-deep">{error}</div>
              )}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-body">Email</label>
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-body">Password</label>
                <Input
                  type="password"
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Sign In
              </Button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-hairline" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-canvas px-2 text-mute">or</span>
              </div>
            </div>

            <Button variant="outline" className="w-full" onClick={handleDemo} disabled={loading}>
              Try Demo Mode
            </Button>

            <p className="mt-6 text-center text-sm text-body">
              Don&apos;t have an account?{" "}
              <Link href="/register" className="font-medium text-link hover:underline">
                Get started
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
