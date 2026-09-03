"use client";

import { Filter, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { AdminAnalyticsFilters, AdminFilterOptions } from "@/types";

interface FilterBarProps {
  filters: AdminAnalyticsFilters;
  options: AdminFilterOptions | null;
  onChange: (filters: AdminAnalyticsFilters) => void;
}

const ALL = "__all__";

export function FilterBar({ filters, options, onChange }: FilterBarProps) {
  const set = (key: keyof AdminAnalyticsFilters, value: string) => {
    onChange({ ...filters, [key]: value === ALL ? undefined : value });
  };

  const activeCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="rounded-xl border border-hairline bg-canvas p-4 shadow-card">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-sm font-medium text-ink">
          <Filter className="h-4 w-4 text-mute" />
          Filters
          {activeCount > 0 && (
            <span className="ml-1 rounded-full bg-canvas-soft2 px-1.5 py-0.5 text-xs text-body">{activeCount}</span>
          )}
        </div>
        {activeCount > 0 && (
          <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => onChange({})}>
            <X className="mr-1 h-3 w-3" /> Clear all
          </Button>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
        <div>
          <label className="mb-1 block text-xs font-medium text-mute">From</label>
          <Input type="date" value={filters.start_date || ""} onChange={(e) => set("start_date", e.target.value)} className="h-9 text-sm" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-mute">To</label>
          <Input type="date" value={filters.end_date || ""} onChange={(e) => set("end_date", e.target.value)} className="h-9 text-sm" />
        </div>

        <FilterSelect
          label="Provider"
          value={filters.provider_name}
          options={options?.providers || []}
          onChange={(v) => set("provider_name", v)}
        />
        <FilterSelect
          label="Program"
          value={filters.training_program_id}
          options={(options?.programs || []).map((p) => ({ value: p.id, label: p.name }))}
          onChange={(v) => set("training_program_id", v)}
        />
        <FilterSelect
          label="Career Domain"
          value={filters.career_domain}
          options={options?.career_domains || []}
          onChange={(v) => set("career_domain", v)}
        />
        <FilterSelect
          label="Location"
          value={filters.location}
          options={options?.locations || []}
          onChange={(v) => set("location", v)}
        />
        <FilterSelect
          label="Employment Status"
          value={filters.employment_status}
          options={(options?.employment_statuses || []).map((s) => ({ value: s, label: s.replace("_", " ") }))}
          onChange={(v) => set("employment_status", v)}
        />
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value?: string;
  options: string[] | { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  const normalized = options.map((o) => (typeof o === "string" ? { value: o, label: o } : o));
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-mute">{label}</label>
      <Select value={value || ALL} onValueChange={onChange}>
        <SelectTrigger className="h-9 text-sm capitalize">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>All</SelectItem>
          {normalized.map((o) => (
            <SelectItem key={o.value} value={o.value} className="capitalize">
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
