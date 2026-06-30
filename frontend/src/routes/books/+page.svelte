<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import {
		project,
		jobStatus,
		isJobRunning,
		jobLogs,
		appendLog,
		clearLogs
	} from '$lib/stores';
	import type { ProjectSummary, ProjectState } from '$lib/api';
	import BookCard from '$lib/components/BookCard.svelte';
	import StageIndicator from '$lib/components/StageIndicator.svelte';
	import OutlineGrid from '$lib/components/OutlineGrid.svelte';
	import LogPanel from '$lib/components/LogPanel.svelte';

	// ── Project list ──────────────────────────────────────────────────────
	let summaries: ProjectSummary[] = [];
	let loadingList = true;
	let listError = '';

	// ── Selected / detail ─────────────────────────────────────────────────
	let detail: ProjectState | null = null;
	let loadingDetail = false;
	let detailError = '';

	// ── Pipeline actions ──────────────────────────────────────────────────
	let actionError = '';
	let actionMsg = '';
	let writeCount = 1;

	$: stage = detail?.stage ?? null;
	$: currentPath = detail?.path ?? null;

	$: computedWrittenIds = (() => {
		const ids = new Set<number>();
		if (!detail?.outline) return ids;
		let count = 0;
		const target = detail.written_scenes ?? 0;
		for (const ch of detail.outline) {
			for (const sc of ch.scenes) {
				if (count < target) { ids.add(sc.scene_id); count++; }
			}
		}
		return ids;
	})();

	// Which card's project is currently running a job?
	$: runningPath = $isJobRunning ? $jobStatus.job_name : null;
	// (job_name isn't the path; but we track it via detail.path === current project)
	$: detailIsRunning = $isJobRunning && detail?.path === $project.path;

	// ── Load list ─────────────────────────────────────────────────────────
	async function refreshList() {
		loadingList = true;
		listError = '';
		try {
			const res = await api.listProjects();
			summaries = res.projects;
		} catch (e: unknown) {
			listError = e instanceof Error ? e.message : String(e);
		} finally {
			loadingList = false;
		}
	}

	// ── Load a project into the detail panel ─────────────────────────────
	async function selectProject(summary: ProjectSummary) {
		if (loadingDetail) return;
		loadingDetail = true;
		detailError = '';
		actionError = '';
		actionMsg = '';
		try {
			await api.loadProject(summary.path);
			const state = await api.projectState();
			detail = state;
			project.set(state);
			// Update is_current in summaries without a full reload
			summaries = summaries.map((s) => ({ ...s, is_current: s.path === summary.path }));
		} catch (e: unknown) {
			detailError = e instanceof Error ? e.message : String(e);
		} finally {
			loadingDetail = false;
		}
	}

	// ── Pipeline actions ──────────────────────────────────────────────────
	async function runAction(fn: () => Promise<unknown>) {
		if ($isJobRunning) { actionError = 'A job is already running.'; return; }
		actionError = '';
		actionMsg = '';
		clearLogs();
		try {
			await fn();
		} catch (e: unknown) {
			actionError = e instanceof Error ? e.message : String(e);
		}
	}

	async function refreshDetail() {
		if (!detail) return;
		try {
			const state = await api.projectState();
			detail = state;
			project.set(state);
		} catch {}
	}

	// Refresh detail + list when a job finishes
	$: if ($jobStatus.status === 'done' || $jobStatus.status === 'error') {
		refreshDetail();
		refreshList();
	}

	onMount(() => {
		refreshList();
		// If a project is already open (e.g., user navigated here after create),
		// automatically open its detail panel
		if ($project.loaded) {
			detail = $project as ProjectState;
		}
	});
</script>

<svelte:head>
	<title>Books — NovelWriter UI</title>
</svelte:head>

<div class="flex h-[calc(100vh-3rem)]">

	<!-- ── LEFT: Book list ──────────────────────────────────────────────── -->
	<aside class="w-72 flex-shrink-0 border-r border-border flex flex-col bg-base-900">
		<div class="flex items-center justify-between px-4 py-3 border-b border-border">
			<h2 class="text-sm font-semibold text-ink-200">Your Books</h2>
			<button
				class="btn-ghost text-xs py-1"
				on:click={refreshList}
				title="Refresh list"
			>↺</button>
		</div>

		<div class="flex-1 overflow-y-auto p-3 space-y-2">
			{#if loadingList}
				<p class="text-xs text-ink-600 px-2 py-4 text-center">Loading…</p>

			{:else if listError}
				<p class="text-xs text-red-400 px-2">{listError}</p>

			{:else if summaries.length === 0}
				<div class="px-2 py-8 text-center space-y-2">
					<p class="text-ink-600 text-xs">No books yet.</p>
					<a href="/" class="btn-primary text-xs inline-flex">+ Create your first novel</a>
				</div>

			{:else}
				{#each summaries as s (s.path)}
					<BookCard
						project={s}
						selected={detail?.path === s.path}
						jobRunning={$isJobRunning && detail?.path === s.path && s.is_current}
						on:click={() => selectProject(s)}
					/>
				{/each}
			{/if}
		</div>

		<div class="border-t border-border p-3">
			<a href="/" class="btn-ghost text-xs w-full justify-center">+ New Novel</a>
		</div>
	</aside>

	<!-- ── RIGHT: Detail panel ──────────────────────────────────────────── -->
	<div class="flex-1 flex flex-col overflow-hidden">

		{#if !detail && !loadingDetail}
			<!-- Empty state -->
			<div class="flex-1 flex flex-col items-center justify-center text-center space-y-3 p-8">
				<span class="text-5xl opacity-20">📚</span>
				<p class="text-ink-500 text-sm max-w-xs">
					Select a book from the list to view its status, pipeline, and content.
				</p>
				<a href="/" class="btn-primary text-sm">Create a new novel →</a>
			</div>

		{:else if loadingDetail}
			<div class="flex-1 flex items-center justify-center">
				<span class="spinner w-5 h-5"></span>
				<span class="text-ink-500 text-sm ml-3">Loading…</span>
			</div>

		{:else if detail}
			<!-- Header -->
			<div class="flex items-center justify-between px-5 py-3 border-b border-border bg-base-900 flex-shrink-0">
				<div>
					<h1 class="text-base font-semibold text-ink-100">
						{detail.name?.replace(/-/g, ' ')}
					</h1>
					<p class="text-[11px] text-ink-600 truncate max-w-xs">{detail.path}</p>
				</div>
				<div class="flex items-center gap-2">
					{#if detailIsRunning}
						<span class="flex items-center gap-1.5 text-xs text-violet-400">
							<span class="spinner w-3.5 h-3.5"></span>
							{$jobStatus.job_name ?? 'processing…'}
						</span>
					{/if}
					<button class="btn-ghost text-xs" on:click={refreshDetail}>↺ Refresh</button>
				</div>
			</div>

			<!-- Main scrollable area -->
			<div class="flex-1 overflow-y-auto">
				<div class="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-0 h-full">

					<!-- Pipeline sidebar -->
					<div class="border-r border-border bg-base-900/50 p-4 space-y-5">
						<div>
							<p class="label mb-3">Pipeline</p>
							<StageIndicator {stage} />
						</div>

						{#if (detail.total_scenes ?? 0) > 0}
							<div>
								<p class="label mb-2">Progress</p>
								<p class="text-xs text-ink-300">
									{detail.written_scenes ?? 0} / {detail.total_scenes} scenes
								</p>
								<div class="mt-2 h-1.5 rounded-full bg-base-700 overflow-hidden">
									<div class="h-full rounded-full bg-violet-600 transition-all"
										style="width: {detail.total_scenes ? Math.round(((detail.written_scenes??0)/detail.total_scenes)*100) : 0}%"></div>
								</div>
							</div>
						{/if}

						<!-- Action buttons -->
						<div class="space-y-2">
							<p class="label">Actions</p>

							{#if stage === 'imported' || (detail.is_imported && stage === 'init')}
								<button class="btn-primary w-full text-xs"
									on:click={() => runAction(api.analyze)}
									disabled={$isJobRunning}>
									{#if $isJobRunning}<span class="spinner w-3.5 h-3.5"></span>{/if}
									🔍 Analyse Content
								</button>

							{:else if stage === 'init'}
								<button class="btn-primary w-full text-xs"
									on:click={() => runAction(api.init)}
									disabled={$isJobRunning}>
									{#if $isJobRunning}<span class="spinner w-3.5 h-3.5"></span>{/if}
									🌱 Generate Plot & Characters
								</button>

							{:else if stage === 'outline'}
								<button class="btn-primary w-full text-xs"
									on:click={() => runAction(api.outline)}
									disabled={$isJobRunning}>
									{#if $isJobRunning}<span class="spinner w-3.5 h-3.5"></span>{/if}
									📋 Generate Outline
								</button>

							{:else if stage === 'write' || stage === 'done'}
								<div class="flex items-center gap-2">
									<input type="number" class="input w-16 text-center py-1.5 text-xs"
										bind:value={writeCount} min="1" max="10" />
									<button class="btn-primary flex-1 text-xs"
										on:click={() => runAction(() => api.write(writeCount))}
										disabled={$isJobRunning}>
										{#if $isJobRunning}<span class="spinner w-3.5 h-3.5"></span>{/if}
										✍️ Write scenes
									</button>
								</div>
							{/if}

							{#if $isJobRunning && detail.path === $project.path}
								<button
									class="btn-ghost text-xs text-amber-400/70 hover:text-amber-400 w-full"
									on:click={async () => {
										await api.resetJob();
										jobStatus.update((s) => ({ ...s, status: 'idle', is_running: false }));
									}}>
									⚡ Reset stuck job
								</button>
							{/if}

							{#if detailError || actionError}
								<p class="text-xs text-red-400 leading-tight">{detailError || actionError}</p>
							{/if}
							{#if actionMsg}
								<p class="text-xs text-green-400">{actionMsg}</p>
							{/if}
						</div>
					</div>

					<!-- Content area -->
					<div class="flex flex-col overflow-hidden">
						<div class="flex-1 overflow-y-auto p-5 space-y-5">

							<!-- Imported notice -->
							{#if detail.is_imported && (stage === 'imported' || stage === 'init')}
								<div class="card p-4 border-amber-800/30 bg-amber-950/10 space-y-1">
									<p class="text-xs font-medium text-amber-400">📥 Imported project</p>
									<p class="text-xs text-ink-500">
										Run <strong class="text-amber-300">Analyse Content</strong> to extract plot,
										characters, and world using AI.
									</p>
								</div>
							{/if}

							<!-- Plot preview -->
							{#if detail.plot_preview}
								<div class="card overflow-hidden">
									<div class="px-4 py-2.5 bg-base-800 border-b border-border flex items-center justify-between">
										<h3 class="text-xs font-semibold text-ink-300 uppercase tracking-widest">Plot</h3>
										<button
											class="text-[10px] px-2 py-0.5 rounded bg-violet-900/30 text-violet-400
											       hover:bg-violet-800/40 hover:text-violet-200 disabled:opacity-30"
											disabled={$isJobRunning}
											on:click={() => runAction(api.regenPlot)}
											title="Regenerate plot, characters & world">↺ Regen</button>
									</div>
									<div class="p-4">
										<p class="text-sm text-ink-300 leading-relaxed whitespace-pre-wrap line-clamp-6">
											{detail.plot_preview}{#if (detail.plot_preview?.length ?? 0) >= 700}…{/if}
										</p>
									</div>
								</div>
							{/if}

							<!-- Characters -->
							{#if (detail.characters?.length ?? 0) > 0}
								<div class="card overflow-hidden">
									<div class="px-4 py-2.5 bg-base-800 border-b border-border flex items-center justify-between">
										<h3 class="text-xs font-semibold text-ink-300 uppercase tracking-widest">
											Characters ({detail.characters?.length})
										</h3>
									</div>
									<div class="p-4 flex flex-wrap gap-2">
										{#each detail.characters ?? [] as name}
											<span class="px-2.5 py-1 rounded-full bg-base-800 border border-border text-xs text-ink-300">
												{name}
											</span>
										{/each}
									</div>
								</div>
							{/if}

							<!-- Outline -->
							{#if (detail.outline?.length ?? 0) > 0}
								<div class="card overflow-hidden">
									<div class="px-4 py-2.5 bg-base-800 border-b border-border flex items-center justify-between">
										<h3 class="text-xs font-semibold text-ink-300 uppercase tracking-widest">Outline</h3>
										<button
											class="text-[10px] px-2 py-0.5 rounded bg-violet-900/30 text-violet-400
											       hover:bg-violet-800/40 hover:text-violet-200 disabled:opacity-30"
											disabled={$isJobRunning}
											on:click={() => runAction(api.regenOutline)}
											title="Regenerate entire outline">↺ Regen</button>
									</div>
									<div class="p-4">
										<OutlineGrid
											outline={detail.outline ?? []}
											projectPath={detail.path ?? ''}
											writtenSceneIds={computedWrittenIds}
											jobRunning={$isJobRunning}
											onRegenScene={(id) => runAction(() => api.regenScene(id))}
											onDeleteScene={async (id) => {
												await api.deleteScene(id);
												refreshDetail();
											}}
										/>
									</div>
								</div>
							{/if}

							{#if !detail.plot_preview && !detail.characters?.length && !detail.outline?.length}
								<div class="text-center py-12 text-ink-600 text-sm space-y-2">
									<p>Nothing here yet.</p>
									<p class="text-xs">Use the actions on the left to start generating content.</p>
								</div>
							{/if}
						</div>

						<!-- Log panel anchored to bottom -->
						<div class="flex-shrink-0 px-4 pb-3">
							<LogPanel />
						</div>
					</div>

				</div>
			</div>
		{/if}
	</div>
</div>
