// Stage 5: progress is stored on the device only (no server, no billing).
const KEY = "cloudsim-progress-v1";

export const loadProgress = () => JSON.parse(localStorage.getItem(KEY) || "{}");
export const saveProgress = (p) => localStorage.setItem(KEY, JSON.stringify(p));

export function completeLab(labId, provider) {
  const p = loadProgress();
  p.labs = { ...(p.labs || {}), [labId]: { completedAt: new Date().toISOString(), provider } };
  saveProgress(p);
  return p;
}

// Trainer / class mode: students export this file, trainer imports many of them.
export const exportProgressFile = () =>
  new Blob([JSON.stringify(loadProgress(), null, 2)], { type: "application/json" });
