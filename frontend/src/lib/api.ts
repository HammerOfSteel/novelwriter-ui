/**
 * Typed fetch wrappers for every backend API endpoint.
 * All functions throw on non-2xx responses with an Error whose message
 * contains the detail from the JSON body (FastAPI style).
 */

const BASE = '/api';

/** Emit a debug log if DEBUG_MODE is on in settings. */
function _dbg(label: string, data?: unknown): void {
	try {
		const raw = localStorage.getItem('debug_mode');
		if (raw !== 'true') return;
	} catch {
		return;
	}
	// eslint-disable-next-line no-console
	console.debug(`[API] ${label}`, data !== undefined ? data : '');
}

async function _fetch<T>(
	path: string,
	init?: RequestInit
): Promise<T> {
	_dbg(`→ ${init?.method ?? 'GET'} ${path}`, init?.body ? JSON.parse(init.body as string) : undefined);
	const res = await fetch(BASE + path, {
		headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
		...init
	});
	if (!res.ok) {
		let message = `HTTP ${res.status}`;
		try {
			const body = await res.json();
			message = body.detail ?? body.message ?? JSON.stringify(body);
		} catch {
			message = await res.text();
		}
		_dbg(`✗ ${path}`, message);
		throw new Error(message);
	}
	const data = await res.json() as T;
	_dbg(`← ${path}`, data);
	return data;
}

const post = <T>(path: string, body?: unknown) =>
	_fetch<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined });

const get = <T>(path: string) => _fetch<T>(path);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface StatusResponse {
	ollama: boolean;
	deps: boolean;
	missing_packages: string[];
}

export interface OllamaModelsResponse {
	models: string[];
}

export interface ProjectState {
	loaded: boolean;
	path?: string;
	name?: string;
	stage?: 'init' | 'outline' | 'write' | 'done' | 'imported';
	is_imported?: boolean;
	plot_preview?: string;
	characters?: string[];
	outline?: Chapter[];
	total_scenes?: number;
	written_scenes?: number;
}

export interface Chapter {
	chapter_id: number;
	chapter_title: string;
	scenes: Scene[];
}

export interface Scene {
	scene_id: number;
	title?: string;
	summary?: string;
	location?: string;
	characters_present?: string[];
	emotional_tone?: string;
}

export interface ScanResult {
	type: 'novelwriter' | 'generic' | 'empty' | 'invalid';
	error?: string;
	// NovelWriter
	has_plot?: boolean;
	has_outline?: boolean;
	has_drafts?: boolean;
	has_characters?: boolean;
	has_world?: boolean;
	// Generic
	chapters?: ScannedChapter[];
	root_files?: ScannedFile[];
	total_files?: number;
	total_words?: number;
}

export interface ScannedChapter {
	name: string;
	files: ScannedFile[];
	words: number;
}

export interface ScannedFile {
	path: string;
	name: string;
	words: number;
}

export interface Settings {
	BACKEND_TYPE: 'ollama' | 'api';
	OLLAMA_BASE_URL: string;
	DEFAULT_MODEL: string;
	CONTEXT_LENGTH_SIZE: number;
	THINK_MODE: string | boolean;
	API_URL: string;
	API_KEY: string;
	API_MODEL: string;
	DEBUG_MODE: boolean;
	NOVEL_VIEWPOINT: string;
	NOVEL_STYLE: string;
	MAX_CONTEXT_CHARS: number;
	NOVEL_LANGUAGE: string;
	project_path: string | null;
}

export interface TestConnectionResult {
	status: 'ok' | 'warn' | 'error';
	message: string;
	models: string[];
}

export interface JobStatus {
	status: 'idle' | 'running' | 'done' | 'error';
	job_name: string | null;
	is_running: boolean;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export const api = {
	// Status
	status: () => get<StatusResponse>('/status'),
	installPrereqs: () => post<{ success: boolean; output: string }>('/prereqs/install'),

	// Ollama
	models: () => get<OllamaModelsResponse>('/ollama/models'),

	// Project
	projectState: () => get<ProjectState>('/project/state'),
	newProject: (body: { idea: string; folder_name?: string; project_dir?: string }) =>
		post<{ success: boolean; path: string; name: string; stage: string }>('/project/new', body),
	loadProject: (path: string) =>
		post<{ success: boolean; path: string; name: string; stage: string }>('/project/load', { path }),
	scanDirectory: (path: string) => post<ScanResult>('/project/scan', { path }),
	importProject: (body: { source_path: string; project_name?: string; project_dir?: string }) =>
		post<{
			success: boolean;
			path: string;
			name: string;
			stage: string;
			scene_count?: number;
			message?: string;
		}>('/project/import', body),
	closeProject: () => post<{ success: boolean }>('/project/close'),
	browseFolder: () =>
		get<{ cancelled: boolean; path: string | null }>('/project/browse'),

	// Pipeline
	init: () => post<{ queued: boolean; job: string }>('/init'),
	outline: () => post<{ queued: boolean; job: string }>('/outline'),
	write: (count = 1) => post<{ queued: boolean; job: string }>('/write', { count }),
	reconstruct: (scene_id: number) =>
		post<{ queued: boolean; job: string }>('/reconstruct', { scene_id }),
	analyze: () => post<{ queued: boolean; job: string }>('/analyze'),

	// Settings
	getSettings: () => get<Settings>('/settings'),
	saveSettings: (body: Partial<Settings>) => post<{ success: boolean; config: Settings }>('/settings', body),
	testConnection: (body: { BACKEND_TYPE?: string; OLLAMA_BASE_URL?: string; API_URL?: string; API_KEY?: string }) =>
		post<TestConnectionResult>('/test-connection', body),

	// Job status & control
	jobStatus: () => get<JobStatus>('/job/status'),
	resetJob: () => post<{ ok: boolean; was: string }>('/job/reset'),
};
