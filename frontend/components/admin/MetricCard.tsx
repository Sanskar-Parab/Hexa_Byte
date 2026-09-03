import { type LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { formatPercent } from "@/lib/utils";

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number | null;
  isPercent?: boolean;
  meta?: string;
}

export function MetricCard({ icon: Icon, label, value, isPercent, meta }: MetricCardProps) {
  const display = isPercent ? formatPercent(value as number | null) : value ?? "No data";
  const noData = value === null || value === undefined;

  return (
    <Card>
      <CardContent className="p-4 sm:p-5">
        <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-mute">
          <Icon className="h-3.5 w-3.5" />
          {label}
        </div>
        <div className={noData ? "text-lg font-medium text-mute" : "text-2xl font-semibold tracking-tight text-ink"}>
          {display}
        </div>
        {meta && <div className="mt-1 text-xs text-body">{meta}</div>}
      </CardContent>
    </Card>
  );
}
