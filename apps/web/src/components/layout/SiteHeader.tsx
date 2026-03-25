import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container px-4 py-3 flex items-center justify-between gap-4">
        <Link href="/" className="font-semibold tracking-tight text-foreground">
          Retail Decision Copilot
        </Link>

        <nav className="flex items-center gap-6 text-sm text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <Link href="/app" className="hover:text-foreground transition-colors">
            Analyst Workspace
          </Link>
          <Link href="/about" className="hover:text-foreground transition-colors">
            About
          </Link>
        </nav>
      </div>
    </header>
  );
}

