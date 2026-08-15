import { Avatar } from "@/components/data-display/Avatar";
import { cx } from "@/utils/cx";

import styles from "./Activity.module.css";

export interface ActorProps {
  name: string;
  src?: string;
  className?: string;
}

export function Actor({ name, src, className }: ActorProps) {
  return (
    <span className={cx(styles.actor, className)}>
      <Avatar name={name} {...(src ? { src } : {})} size="sm" />
      {name}
    </span>
  );
}
