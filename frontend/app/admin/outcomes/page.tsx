"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Users, GraduationCap, Briefcase, Building2, TrendingUp, TrendingDown,
  Wallet, UserCheck, UserX, UserMinus, ShieldCheck, Target,
} from "lucide-react";
import Link from "next/link";
import { SectionHeader } from "@/components/ui/section-header";
import { LoadingState } from "@/components/ui/loading-state";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/admin/MetricCard";
import { FilterBar } from "@/components/admin/FilterBar";
import { RetentionChart } from "@/components/admin/RetentionChart";
import { SkillGapChart } from "@/components/admin/SkillGapChart";
import { NonPlacementChart } from "@/components/admin/NonPlacementChart";
import { ProviderTable } from "@/components/admin/ProviderTable";
import { ProgramTable } from "@/components/admin/ProgramTable";
import { CurriculumRecommendations } from "@/components/admin/CurriculumRecommendations";
import { DemoDatasetBanner } from "@/components/admin/DemoDatasetBanner";
import { VerificationQueue } from "@/components/admin/VerificationQueue";
import { formatCurrency } from "@/lib/utils";
import { api } from "@/lib/api";
import type {
  CohortMetrics, ProviderComparisonRow, ProgramAnalyticsRow,
  SkillGapRow, NonPlacementCategoryRow, CurriculumRecommendationRow,
  AdminFilterOptions, AdminAnalyticsFilters,
} from "@/types";

export default function AdminOutcomesPage() {
  const [filters, setFilters] = useState<AdminAnalyticsFilters>({});
  const [filterOptions, setFilterOptions] = useState<AdminFilterOptions | null>(null);
  const [overview, setOverview] = useState<CohortMetrics | null>(null);
  const [providers, setProviders] = useState<ProviderComparisonRow[]>([]);
  const [programs, setPrograms] = useState<ProgramAnalyticsRow[]>([]);
  const [skillGaps, setSkillGaps] = useState<SkillGapRow[]>([]);
  const [nonPlacement, setNonPlacement] = useState<NonPlacementCategoryRow[]>([]);
  const [curriculumRecs, setCurriculumRecs] = useState<CurriculumRecommendationRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAdminFilterOptions().then(setFilterOptions).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [ov, prov, prog, gaps, nonPlaced, curriculum] = await Promise.all([
        api.getAdminOverview(filters),
        api.getAdminProviders(filters),
        api.getAdminPrograms(filters),
        api.getAdminSkillGaps(filters),
        api.getAdminNonPlacement(filters),
        api.getAdminCurriculumRecommendations(filters),
      ]);
      setOverview(ov);
      setProviders(prov);
      setPrograms(prog);
      setSkillGaps(gaps);
      setNonPlacement(nonPlaced);
      setCurriculumRecs(curriculum);
    } catch (err) {
      setOverview(null);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  const handleLoadDemoData = async () => {
    await api.loadAdminDemoData();
    await load();
    api.getAdminFilterOptions().then(setFilterOptions).catch(() => {});
  };

  return (
    <div className="space-y-8">
      <SectionHeader
        eyebrow="Government Skilling Impact Dashboard"
        title="Training & Employment Outcomes"
        description="Aggregated analytics across every trainee, provider, and program — computed only from stored, verified data. Small cohorts are never ranked or averaged unreliably."
      />

      {!loading && overview && (
        <DemoDatasetBanner
          demoTraineeCount={overview.demo_trainee_count}
          totalTraineeCount={overview.trainee_count}
          onLoadDemoData={handleLoadDemoData}
        />
      )}

      <div className="flex flex-wrap gap-2">
        <Link href="/admin/trainees">
          <Button>+ Add Programme Details</Button>
        </Link>
        <Link href="/admin/identity-reviews">
          <Button variant="outline">View Identity Reviews</Button>
        </Link>
      </div>

      <FilterBar filters={filters} options={filterOptions} onChange={setFilters} />

      {loading && <LoadingState message="Computing analytics..." />}

      {!loading && overview && (
        <>
          <Section title="Overview">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard icon={Users} label="Total Trainees" value={overview.trainee_count} />
              <MetricCard icon={GraduationCap} label="Training Completion" value={overview.training_completion_rate} isPercent />
              <MetricCard icon={Briefcase} label="Placement Rate" value={overview.placement_rate} isPercent />
              <MetricCard icon={UserCheck} label="Non-Placement Rate" value={overview.non_placement_rate} isPercent />
              <MetricCard icon={ShieldCheck} label="Consent Coverage" value={overview.consent_coverage_pct} isPercent
                meta="Trainees with active outcome consent" />
            </div>
            {!overview.sample_size_sufficient && overview.trainee_count > 0 && (
              <p className="mt-3 text-xs text-warn-deep">
                Fewer than 5 trainees match the current filters — rates are suppressed to avoid an unreliable reading.
              </p>
            )}
          </Section>

          <Section title="Training">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <MetricCard icon={GraduationCap} label="Training Completion Rate" value={overview.training_completion_rate} isPercent />
              <MetricCard icon={Target} label="Training-Relevant Employment" value={overview.training_relevant_employment_rate} isPercent
                meta="Employed trainees whose job still matches their training" />
            </div>
          </Section>

          <Section title="Placement">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <MetricCard icon={Briefcase} label="Placement Rate" value={overview.placement_rate} isPercent />
              <MetricCard icon={UserCheck} label="Non-Placement Rate" value={overview.non_placement_rate} isPercent />
            </div>
            <div className="mt-4">
              <NonPlacementChart categories={nonPlacement} />
            </div>
          </Section>

          <Section title="Employment">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard icon={Briefcase} label="Employment Rate" value={overview.employment_rate} isPercent />
              <MetricCard icon={Building2} label="Self Employment Rate" value={overview.self_employment_rate} isPercent />
              <MetricCard icon={UserCheck} label="Unemployment Rate" value={overview.unemployment_rate} isPercent />
              <MetricCard icon={UserX} label="Unreachable Rate" value={overview.unreachable_rate} isPercent />
              <MetricCard icon={UserMinus} label="Declined to Respond Rate" value={overview.declined_to_respond_rate} isPercent />
              <MetricCard
                icon={overview.wage_growth_percentage !== null && overview.wage_growth_percentage < 0 ? TrendingDown : TrendingUp}
                label="Wage Growth"
                value={overview.wage_growth_percentage}
                isPercent
              />
              <MetricCard
                icon={Wallet}
                label="Average Starting Salary"
                value={overview.average_starting_salary === null ? null : formatCurrency(overview.average_starting_salary)}
              />
              <MetricCard
                icon={Wallet}
                label="Average Current Salary"
                value={overview.average_current_salary === null ? null : formatCurrency(overview.average_current_salary)}
              />
            </div>
          </Section>

          <Section title="Retention">
            <RetentionChart metrics={overview} />
          </Section>

          <Section title="Skills">
            <SkillGapChart gaps={skillGaps} />
          </Section>

          <Section title="Adaptive Insights">
            <CurriculumRecommendations recommendations={curriculumRecs} />
          </Section>

          <Section title="Provider Performance">
            <ProviderTable providers={providers} />
          </Section>

          <Section title="Program Impact">
            <ProgramTable programs={programs} />
          </Section>

          <Section title="Employer Verification">
            <VerificationQueue />
          </Section>
        </>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="mb-3 text-lg font-semibold tracking-tight text-ink">{title}</h2>
      {children}
    </div>
  );
}
