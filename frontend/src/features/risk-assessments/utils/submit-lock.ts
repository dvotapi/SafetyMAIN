/**
 * Submit lock that stays acquired after success so a second click
 * before unmount cannot start another create.
 */
export type SubmitLock = {
  tryAcquire: () => boolean;
  release: () => void;
  isLocked: () => boolean;
};

export function createSubmitLock(): SubmitLock {
  let locked = false;
  return {
    tryAcquire: () => {
      if (locked) {
        return false;
      }
      locked = true;
      return true;
    },
    release: () => {
      locked = false;
    },
    isLocked: () => locked,
  };
}
