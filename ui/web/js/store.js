const listeners = new Set();
export const state = {
  copy: null,
  setup: null,
  project: null,
  projectPath: null,
  presets: null,
  safezones: null,
  job: null,
};

export function setState(patch) {
  Object.assign(state, patch);
  listeners.forEach((fn) => fn(state));
}

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
