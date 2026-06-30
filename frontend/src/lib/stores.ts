/**
 * Svelte writable stores for global application state.
 */
import { writable, derived } from 'svelte/store';
import type { ProjectState, Settings, StatusResponse, JobStatus } from './api';

// ---------------------------------------------------------------------------
// System status (prereqs, Ollama)
// ---------------------------------------------------------------------------
export const sysStatus = writable<StatusResponse | null>(null);

// ---------------------------------------------------------------------------
// Current project
// ---------------------------------------------------------------------------
export const project = writable<ProjectState>({ loaded: false });

export const isProjectLoaded = derived(project, ($p) => $p.loaded);

export const projectStage = derived(project, ($p) => $p.stage ?? null);

// ---------------------------------------------------------------------------
// Job / log stream
// ---------------------------------------------------------------------------
export type LogEntry =
	| { type: 'log'; message: string }
	| { type: 'done'; message: string }
	| { type: 'error'; message: string }
	| { type: 'heartbeat' };

export const jobStatus = writable<JobStatus>({
	status: 'idle',
	job_name: null,
	is_running: false
});

export const jobLogs = writable<LogEntry[]>([]);

export const isJobRunning = derived(jobStatus, ($j) => $j.is_running);

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------
export const settings = writable<Settings | null>(null);

// ---------------------------------------------------------------------------
// UI state
// ---------------------------------------------------------------------------
export const logPanelOpen = writable<boolean>(true);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Append a single log entry and cap the list at 500. */
export function appendLog(entry: LogEntry) {
	jobLogs.update((logs) => {
		const updated = [...logs, entry];
		return updated.length > 500 ? updated.slice(-500) : updated;
	});
}

/** Clear the log panel. */
export function clearLogs() {
	jobLogs.set([]);
}
