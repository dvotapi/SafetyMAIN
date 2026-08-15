"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import {
  Alert,
  Button,
  EmptyState,
  LoadingState,
  ObjectHeader,
  ObjectTabs,
  SideDrawer,
  StatusBadge,
  Text,
  useToast,
} from "@/components";
import { PageContainer } from "@/components/patterns/Page";
import {
  useActivateHazardMutation,
  useArchiveHazardMutation,
  useRestoreHazardMutation,
  useUpdateHazardMutation,
} from "@/features/hazards/api/hazard-mutations";
import {
  useHazardActivityQuery,
  useHazardDetailQuery,
  useRelatedRiskAssessmentsQuery,
} from "@/features/hazards/api/hazard-queries";
import { HazardActivity } from "@/features/hazards/components/hazard-activity";
import { HazardConflictDialog } from "@/features/hazards/components/hazard-conflict-dialog";
import { HazardForm } from "@/features/hazards/components/hazard-form";
import { HazardLifecycleActions } from "@/features/hazards/components/hazard-lifecycle-actions";
import {
  HazardRelatedAssessments,
  HazardRiskSummary,
} from "@/features/hazards/components/hazard-related-assessments";
import {
  HazardProperties,
  HazardSummary,
} from "@/features/hazards/components/hazard-summary";
import {
  canEditHazardFields,
  canEditHazardSource,
  canCreateRiskAssessmentForHazard,
  mapHazardCapabilities,
} from "@/features/hazards/hooks/use-hazard-permissions";
import {
  formValuesToUpdateRequest,
  hazardToFormValues,
} from "@/features/hazards/mappers/hazard-mappers";
import {
  hazardFormSchema,
  type HazardFormValues,
} from "@/features/hazards/schemas/hazard-form-schema";
import type { HazardLifecycleAction } from "@/features/hazards/types/hazard-types";
import { hazardStatusToVisual } from "@/features/hazards/utils/hazard-status";
import { useAuth } from "@/hooks/auth";
import {
  ConflictError,
  NotFoundError,
  PermissionError,
  toUserSafeMessage,
} from "@/services/api/errors";

export function HazardObjectPage({ hazardId }: { hazardId: string }) {
  const { hasPermission } = useAuth();
  const capabilities = mapHazardCapabilities(hasPermission);
  const { toast } = useToast();
  const detail = useHazardDetailQuery(hazardId, capabilities.canRead);
  const related = useRelatedRiskAssessmentsQuery(
    hazardId,
    capabilities.canViewRelatedAssessments && detail.isSuccess,
  );
  const activity = useHazardActivityQuery(
    hazardId,
    capabilities.canViewActivity && detail.isSuccess,
  );
  const updateMutation = useUpdateHazardMutation(hazardId);
  const activateMutation = useActivateHazardMutation(hazardId);
  const archiveMutation = useArchiveHazardMutation(hazardId);
  const restoreMutation = useRestoreHazardMutation(hazardId);

  const [tab, setTab] = useState("overview");
  const [editOpen, setEditOpen] = useState(false);
  const [conflictOpen, setConflictOpen] = useState(false);
  const [lifecycleError, setLifecycleError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<HazardLifecycleAction | null>(
    null,
  );

  const form = useForm<HazardFormValues>({
    resolver: zodResolver(hazardFormSchema),
    mode: "onSubmit",
  });

  const hazard = detail.data;

  useEffect(() => {
    if (hazard) {
      document.title = `${hazard.code} · SafetyMAIN`;
    } else {
      document.title = "Hazard · SafetyMAIN";
    }
  }, [hazard]);

  useEffect(() => {
    if (hazard && editOpen) {
      form.reset(hazardToFormValues(hazard));
    }
  }, [hazard, editOpen, form]);

  const editable = useMemo(
    () => (hazard ? canEditHazardFields(hazard, capabilities) : false),
    [hazard, capabilities],
  );
  const sourceEditable = useMemo(
    () => (hazard ? canEditHazardSource(hazard, capabilities) : false),
    [hazard, capabilities],
  );
  const canCreateRiskAssessment = useMemo(
    () =>
      hazard ? canCreateRiskAssessmentForHazard(hazard, capabilities) : false,
    [hazard, capabilities],
  );

  if (!capabilities.canRead) {
    return (
      <PageContainer variant="object">
        <EmptyState
          title="Hazard unavailable"
          description="You do not have permission to view hazards."
        />
      </PageContainer>
    );
  }

  if (detail.isLoading) {
    return (
      <PageContainer variant="object">
        <LoadingState label="Loading hazard" />
      </PageContainer>
    );
  }

  if (detail.isError) {
    if (detail.error instanceof NotFoundError) {
      return (
        <PageContainer variant="object">
          <EmptyState
            title="Hazard not found"
            description="The hazard does not exist or is not available in this organization."
            action={
              <Button asChild variant="secondary">
                <Link href="/safety/hazards">Back to registry</Link>
              </Button>
            }
          />
        </PageContainer>
      );
    }
    if (detail.error instanceof PermissionError) {
      return (
        <PageContainer variant="object">
          <EmptyState
            title="Access denied"
            description={toUserSafeMessage(detail.error)}
          />
        </PageContainer>
      );
    }
    return (
      <PageContainer variant="object">
        <div style={{ display: "grid", gap: 8 }}>
          <Alert tone="danger" title="Unable to load hazard">
            {toUserSafeMessage(detail.error)}
          </Alert>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void detail.refetch()}
          >
            Retry
          </Button>
        </div>
      </PageContainer>
    );
  }

  if (!hazard) {
    return null;
  }

  async function onSave(values: HazardFormValues) {
    if (!hazard) {
      return;
    }
    try {
      await updateMutation.mutateAsync(
        formValuesToUpdateRequest(values, hazard.version, {
          includeSource: sourceEditable,
        }),
      );
      toast({ tone: "success", title: "Hazard updated" });
      setEditOpen(false);
    } catch (error) {
      if (error instanceof ConflictError) {
        setConflictOpen(true);
        return;
      }
      form.setError("root", { message: toUserSafeMessage(error) });
    }
  }

  async function runLifecycle(
    action: HazardLifecycleAction,
    runner: () => Promise<unknown>,
    successTitle: string,
  ) {
    setLifecycleError(null);
    setBusyAction(action);
    try {
      await runner();
      toast({ tone: "success", title: successTitle });
    } catch (error) {
      if (error instanceof ConflictError) {
        setConflictOpen(true);
      } else {
        setLifecycleError(toUserSafeMessage(error));
      }
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <PageContainer variant="object">
      <ObjectHeader
        title={hazard.title}
        subtitle={hazard.code}
        status={<StatusBadge status={hazardStatusToVisual(hazard.status)} />}
        meta={
          <Text tone="muted" variant="caption">
            Version {hazard.version}
          </Text>
        }
        actions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {editable ? (
              <Button variant="secondary" onClick={() => setEditOpen(true)}>
                Edit hazard
              </Button>
            ) : null}
            {canCreateRiskAssessment ? (
              <Button asChild variant="secondary">
                <Link
                  href={`/safety/risk-assessments/new?hazardId=${encodeURIComponent(hazard.id)}`}
                >
                  Create Risk Assessment
                </Link>
              </Button>
            ) : null}
            <Button asChild variant="ghost">
              <Link href="/safety/hazards">Back to registry</Link>
            </Button>
          </div>
        }
      />

      <HazardSummary hazard={hazard} />
      <HazardLifecycleActions
        hazard={hazard}
        capabilities={capabilities}
        busyAction={busyAction}
        errorMessage={lifecycleError}
        onActivate={() =>
          runLifecycle(
            "activate",
            () => activateMutation.mutateAsync(hazard.version),
            "Hazard activated",
          )
        }
        onArchive={(reason) =>
          runLifecycle(
            "archive",
            () =>
              archiveMutation.mutateAsync({
                expectedVersion: hazard.version,
                reason,
              }),
            "Hazard archived",
          )
        }
        onRestore={(reason) =>
          runLifecycle(
            "restore",
            () =>
              restoreMutation.mutateAsync({
                expectedVersion: hazard.version,
                reason,
              }),
            "Hazard restored",
          )
        }
      />

      <ObjectTabs
        tabs={[
          { id: "overview", label: "Overview" },
          { id: "risk", label: "Risk assessments" },
          { id: "activity", label: "Activity" },
        ]}
        activeTabId={tab}
        onTabChange={setTab}
      />

      {tab === "overview" ? (
        <div style={{ display: "grid", gap: "var(--sm-space-4)" }}>
          <HazardProperties hazard={hazard} />
          {capabilities.canViewRelatedAssessments ? (
            <HazardRiskSummary
              assessments={related.data ?? []}
              loading={related.isLoading}
            />
          ) : null}
        </div>
      ) : null}

      {tab === "risk" ? (
        <HazardRelatedAssessments
          assessments={related.data ?? []}
          loading={related.isLoading}
          canView={capabilities.canViewRelatedAssessments}
        />
      ) : null}

      {tab === "activity" ? (
        <HazardActivity
          items={activity.data ?? []}
          loading={activity.isLoading}
          canView={capabilities.canViewActivity}
        />
      ) : null}

      <SideDrawer
        open={editOpen}
        onOpenChange={setEditOpen}
        title="Edit hazard"
        description="Lifecycle-managed fields are not editable here."
      >
        {form.formState.errors.root?.message ? (
          <Alert tone="danger" title="Could not update hazard">
            {form.formState.errors.root.message}
          </Alert>
        ) : null}
        <HazardForm
          id="hazard-edit-form"
          form={form}
          onSubmit={onSave}
          showCode={false}
          sourceEditable={sourceEditable}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
          <Button variant="secondary" onClick={() => setEditOpen(false)}>
            Cancel
          </Button>
          <Button
            type="submit"
            form="hazard-edit-form"
            loading={updateMutation.isPending}
            disabled={updateMutation.isPending}
          >
            Save changes
          </Button>
        </div>
      </SideDrawer>

      <HazardConflictDialog
        open={conflictOpen}
        onOpenChange={setConflictOpen}
        loading={detail.isFetching}
        onReload={() => {
          void detail.refetch();
        }}
      />
    </PageContainer>
  );
}
