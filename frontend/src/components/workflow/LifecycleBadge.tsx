import {
  StatusBadge,
  type StatusBadgeProps,
} from "@/components/primitives/StatusBadge";

export type LifecycleBadgeProps = StatusBadgeProps;

/** Domain lifecycle status — wraps StatusBadge. */
export function LifecycleBadge(props: LifecycleBadgeProps) {
  return <StatusBadge {...props} />;
}
