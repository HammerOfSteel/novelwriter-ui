<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { project, jobStatus, isJobRunning, clearLogs, debugMode } from '$lib/stores';
	import StageIndicator from '$lib/components/StageIndicator.svelte';
	import OutlineGrid from '$lib/components/OutlineGrid.svelte';
	import LogPanel from '$lib/components/LogPanel.svelte';
	import DebugPanel from '$lib/components/DebugPanel.svelte';

	$: p = $project;
	$: stage = p.stage ?? null;

	// Written scene IDs
	$: writtenSceneIds = (() => {
		const ids = new Set<number>();
		if (!p.outline) return ids;
		const drafts = p.outline.flatMap((ch) => ch.scenes);
		for (const scene of drafts) {
			// In the API response, written = scene_id present in drafts/
			// We determine this from the project state endpoint
		}
		return ids;
	})();

	// Compute written scene IDs from outline + written_scenes count
	// Since the API only gives us count, we mark the first N as written
	// A fuller impl would track individual scene status in the API
	$: computedWrittenIds = (() => {
		const ids = new Set<number>();
		if (!p.outline) return ids;
		let count = 0;
		const target = p.written_scenes ?? 0;
		for (const ch of p.outline) {
			for (const sc of ch.scenes) {
				if (count < target) {
					ids.add(sc.scene_id);
					count++;
				}
			}
		}
		return ids;
	})();

	// Write N count
	let writeCount = 1;
	// Reconstruct scene ID
	let reconstructId = 1;

	// Action feedback
	let actionError = '';
	let actionMsg = '';

	async function runAction(fn: () => Promise<unknown>, successMsg?: string) {
		if ($isJobRunning) { actionError = 'A job is already running.'; return; }
		actionError = '';
		actionMsg = '';
		clearLogs();
		try {
			await fn();
			if (successMsg) actionMsg = successMsg;
		} catch (e: unknown) {
			actionError = e instanceof Error ? e.message : String(e);
		}
	}

	async function refreshProject() {
		try {
			const state = await api.projectState();
			project.set(state);
		} catch {}
	}

	onMount(() => {
		if (!$project.loaded) {
			goto('/');
			return;
		}
		refreshProject();
	});

	// Open a file via the backend
	async function openFile(path: string) {
		try {
			await fetch(`/api/open?path=${encodeURIComponent(path)}`, { method: 'POST' });
		} catch {}
	}
</script>

<svelte:head>
	<title>{p.name ?? 'Project'} — NovelWriter UI</title>
</svelte:head>

{#if !p.loaded}
	<div class="flex items-center justify-center h-64 text-ink-500 text-sm">
		Loading…
	</div>
{:else}
	<div class="flex h-[calc(100vh-3rem)]">

		<!-- ── SIDEBAR ───────────────────────────────────────────────────── -->
		<aside class="w-56 flex-shrink-0 border-r border-border bg-base-900 flex flex-col overflow-y-auto">
			<div class="p-4 border-b border-border space-y-1">
				<h2 class="text-sm font-semibold text-ink-100 truncate">{p.name}</h2>
				<p class="text-[11px] text-ink-500 break-all leading-tight">{p.path}</p>
			</div>

			<!-- Stage pipeline -->
			<div class="p-4 border-b border-border">
				<p class="label mb-3">Pipeline</p>
				<StageIndicator stage={stage} />
			</div>

			<!-- Progress -->
			{#if (p.total_scenes ?? 0) > 0}
				<div class="p-4 border-b border-border space-y-2">
					<p class="label">Progress</p>
					<div class="text-xs text-ink-300">
						{p.written_scenes ?? 0} / {p.total_scenes} scenes
					</div>
					<div class="h-1.5 bg-base-800 rounded-full overflow-hidden">
						<div
							class="h-full bg-violet-600 rounded-full transition-all duration-500"
							style="width: {Math.round(((p.written_scenes ?? 0) / (p.total_scenes ?? 1)) * 100)}%"
						></div>
					</div>
				</div>
			{/if}

			<!-- Nav -->
			<nav class="p-3 space-y-1 flex-1">
				<a href="/" class="btn-ghost text-xs w-full justify-start">← Home</a>
				<button
					class="btn-ghost text-xs w-full justify-start"
					on:click={refreshProject}
				>
					↺ Refresh
				</button>
				<a href="/settings" class="btn-ghost text-xs w-full justify-start">⚙ Settings</a>
				<button
					class="btn-ghost text-xs w-full justify-start text-red-400/70 hover:text-red-400"
					on:click={() => { api.closeProject(); project.set({ loaded: false }); goto('/'); }}
				>
					✕ Close project
				</button>
			</nav>
		</aside>

		<!-- ── MAIN CONTENT ───────────────────────────────────────────────── -->
		<div class="flex-1 flex flex-col overflow-hidden">
			<div class="flex-1 overflow-y-auto p-5 space-y-5">

				<!-- Imported notice -->
				{#if p.is_imported && stage === 'imported'}
					<div class="card p-4 border-violet-800/40 bg-violet-950/20 space-y-2">
						<p class="text-sm font-medium text-violet-300">📥 Imported project</p>
						<p class="text-xs text-ink-500">
							Your files have been copied into this project. Run
							<strong class="text-violet-400">Analyse Content</strong> below to let the AI extract
							the plot, characters, and world from your existing writing.
						</p>
					</div>
				{/if}

				<!-- Plot preview -->
				{#if p.plot_preview}
					<div class="card overflow-hidden">
						<div class="px-4 py-2.5 bg-base-800 border-b border-border">
							<h3 class="text-xs font-semibold text-ink-300 uppercase tracking-widest">Plot</h3>
						</div>
						<div class="p-4">
							<p class="text-sm text-ink-300 leading-relaxed line-clamp-5 whitespace-pre-wrap">
								{p.plot_preview}{#if (p.plot_preview?.length ?? 0) >= 700}…{/if}
							</p>
						</div>
					</div>
				{/if}

				<!-- Characters -->
				{#if (p.characters?.length ?? 0) > 0}
					<div class="card overflow-hidden">
						<div class="px-4 py-2.5 bg-base-800 border-b border-border">
							<h3 class="text-xs font-semibold text-ink-300 uppercase tracking-widest">
								Characters ({p.characters?.length})
							</h3>
						</div>
						<div class="p-4 flex flex-wrap gap-2">
							{#each p.characters ?? [] as name}
								<span class="px-2.5 py-1 rounded-full bg-base-800 border border-border text-xs text-ink-300">
									{name}
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Outline -->
				<div class="card overflow-hidden">
					<div class="px-4 py-2.5 bg-base-800 border-b border-border">
						<h3 class="text-xs font-semibold text-ink-300 uppercase tracking-widest">Outline</h3>
					</div>
					<div class="p-4">
						<OutlineGrid
							outline={p.outline ?? []}
							projectPath={p.path ?? ''}
							writtenSceneIds={computedWrittenIds}
						/>
					</div>
				</div>

			</div>

			<!-- ── ACTION BAR ──────────────────────────────────────────────── -->
			<div class="flex-shrink-0 border-t border-border bg-base-900 px-4 py-3 space-y-2">
				<div class="flex flex-wrap items-center gap-2">

					<!-- Imported: Analyse -->
					{#if stage === 'imported'}
						<button
							class="btn-primary"
							on:click={() => runAction(api.analyze)}
							disabled={$isJobRunning}
						>
							{#if $isJobRunning}
								<span class="spinner w-4 h-4"></span>
							{/if}
							🔍 Analyse Content
						</button>

					<!-- Init stage: Generate Plot -->
					{:else if stage === 'init'}
						<button
							class="btn-primary"
							on:click={() => runAction(api.init)}
							disabled={$isJobRunning}
						>
							{#if $isJobRunning}
								<span class="spinner w-4 h-4"></span>
							{/if}
							🌱 Generate Plot & Characters
						</button>

					<!-- Outline stage: Generate Outline -->
					{:else if stage === 'outline'}
						<button
							class="btn-primary"
							on:click={() => runAction(api.outline)}
							disabled={$isJobRunning}
						>
							{#if $isJobRunning}
								<span class="spinner w-4 h-4"></span>
							{/if}
							📋 Generate Outline
						</button>

					<!-- Write stage: Write scenes -->
					{:else if stage === 'write'}
						{#if (p.written_scenes ?? 0) >= (p.total_scenes ?? 0) && (p.total_scenes ?? 0) > 0}
							<span class="stage-badge bg-green-500/15 text-green-400 border border-green-800/30">
								✓ Novel complete
							</span>
						{:else}
							<button
								class="btn-primary"
								on:click={() => runAction(() => api.write(1))}
								disabled={$isJobRunning}
							>
								{#if $isJobRunning}
									<span class="spinner w-4 h-4"></span>
								{/if}
								✍ Write Next Scene
							</button>

							<div class="flex items-center gap-1.5">
								<input
									type="number"
									class="input w-16 text-center py-1.5"
									bind:value={writeCount}
									min="1"
									max="50"
								/>
								<button
									class="btn-secondary"
									on:click={() => runAction(() => api.write(writeCount))}
									disabled={$isJobRunning}
								>
									Write {writeCount}
								</button>
							</div>

							<div class="flex items-center gap-1.5 ml-2 pl-2 border-l border-border">
								<span class="text-xs text-ink-500">Reconstruct scene</span>
								<input
									type="number"
									class="input w-16 text-center py-1.5"
									bind:value={reconstructId}
									min="1"
								/>
								<button
									class="btn-secondary text-xs"
									on:click={() => runAction(() => api.reconstruct(reconstructId))}
									disabled={$isJobRunning}
								>
									↺ Rebuild state
								</button>
							</div>
						{/if}
					{/if}

					<button
						class="btn-ghost ml-auto text-xs"
						on:click={refreshProject}
					>
						↺ Refresh
					</button>
				</div>

				{#if actionError}
					<p class="text-xs text-red-400">{actionError}</p>
				{/if}
				{#if actionMsg}
					<p class="text-xs text-green-400">{actionMsg}</p>
				{/if}
			</div>

			<!-- Log panel -->
			<div class="flex-shrink-0 px-4 pb-3">
				<LogPanel />
			</div>
		</div>

	</div>
{/if}

<DebugPanel />
