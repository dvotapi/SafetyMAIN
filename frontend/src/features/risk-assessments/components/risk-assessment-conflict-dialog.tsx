"use client";

import {
  Alert,
  Button,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components";

export function RiskAssessmentConflictDialog({
  open,
  onOpenChange,
  onReload,
  loading,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onReload: () => void;
  loading?: boolean;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader
          title="Risk assessment changed elsewhere"
          description="Another user updated this assessment. Your changes were not saved."
        />
        <DialogBody>
          <Alert tone="warning" title="Version conflict">
            Reload the latest version, then re-apply your edits. The mutation
            will not retry automatically.
          </Alert>
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Keep my draft
          </Button>
          <Button
            variant="primary"
            {...(loading ? { loading: true } : {})}
            onClick={() => {
              onReload();
              onOpenChange(false);
            }}
          >
            Reload latest
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
