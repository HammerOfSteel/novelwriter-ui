<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import {
		sysStatus,
		project,
		jobStatus,
		jobLogs,
		appendLog,
		isJobRunning,
		debugMode,
		settings
	} from '$lib/stores';
	import { api } from '$lib/api';

	// Bootstrap: fetch status, project state, and settings on first load
	onMount(async () => {
		try {
			const [status, proj, cfg] = await Promise.all([
				api.status(),
				api.projectState(),
				api.getSettings()
			]);
			sysStatus.set(status);
			project.set(proj);
			settings.set(cfg);
		} catch {
			// Backend might not be ready yet
		}

		// Keep debugMode store subscribed so its localStorage side-effect stays active
		const unsub = debugMode.subscribe(() => {});
		// connectSSE after initial data fetch
		connectSSE();
		return unsub;
	});

	let sseSource: EventSource | null = null;

	function connectSSE() {
		if (sseSource) sseSource.close();
		sseSource = new EventSource('/api/stream');

		sseSource.onmessage = (e) => {
			try {
				const item = JSON.parse(e.data);
				if (item.type === 'heartbeat') return;

				// Debug: log every SSE event when debug mode is on
				if (localStorage.getItem('debug_mode') === 'true') {
					// eslint-disable-next-line no-console
					console.debug('[SSE]', item.type, item.message ?? '');
				}

				appendLog(item);

				if (item.type === 'done' || item.type === 'error') {
					jobStatus.update((s) => ({ ...s, status: item.type, is_running: false }));
					// Refresh project state after job completes
					api.projectState().then((p) => project.set(p)).catch(() => {});
				} else {
					jobStatus.update((s) => ({ ...s, is_running: true, status: 'running' }));
				}
			} catch {
				// Ignore malformed events
			}
		};

		sseSource.onerror = () => {
			if (localStorage.getItem('debug_mode') === 'true') {
				// eslint-disable-next-line no-console
				console.debug('[SSE] connection error — reconnecting in 3s');
			}
			// Reconnect after a short delay
			sseSource?.close();
			setTimeout(connectSSE, 3000);
		};
	}

	// Nav helper
	$: currentPath = $page.url.pathname;
</script>

<div class="min-h-screen flex flex-col">
	<!-- Top navigation bar -->
	<header
		class="sticky top-0 z-50 flex items-center justify-between px-5 h-12
		       bg-base-900/90 backdrop-blur border-b border-border"
	>
		<!-- Logo + title -->
		<a href="/" class="flex items-center gap-2.5 group">
			<img src="/favicon.ico" alt="" class="w-6 h-6 opacity-80 group-hover:opacity-100 transition-opacity" />
			<span class="text-sm font-semibold text-ink-100 tracking-tight">NovelWriter UI</span>
		</a>

		<!-- Nav links -->
		<nav class="flex items-center gap-1">
			<a
				href="/"
				class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
				{currentPath === '/' ? 'bg-violet-600/20 text-violet-400' : 'text-ink-300 hover:text-ink-100 hover:bg-base-800'}"
			>
				Home
			</a>
			<a
				href="/books"
				class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
				{currentPath.startsWith('/books') ? 'bg-violet-600/20 text-violet-400' : 'text-ink-300 hover:text-ink-100 hover:bg-base-800'}"
			>
				Books
			</a>
			<a
				href="/settings"
				class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
				{currentPath === '/settings' ? 'bg-violet-600/20 text-violet-400' : 'text-ink-300 hover:text-ink-100 hover:bg-base-800'}"
			>
				Settings
			</a>
		</nav>

		<!-- Job indicator -->
		{#if $isJobRunning}
			<div class="flex items-center gap-1.5 text-xs text-violet-400">
				<span class="spinner w-3 h-3"></span>
				<span class="hidden sm:inline">{$jobStatus.job_name ?? 'running…'}</span>
			</div>
		{:else}
			<div class="w-20"></div>
		{/if}
	</header>

	<!-- Page content -->
	<main class="flex-1">
		<slot />
	</main>
</div>
