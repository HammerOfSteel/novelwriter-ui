<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { project, sysStatus } from '$lib/stores';
	import PrereqBar from '$lib/components/PrereqBar.svelte';
	import type { ScanResult } from '$lib/api';

	// ── New Novel form ─────────────────────────────────────────────────────
	let idea = '';
	let folderName = '';
	let projectDir = '';
	let creatingProject = false;
	let createError = '';

	// Auto-generate folder name from idea's first line
	$: if (idea) {
		const firstLine = idea.split('\n')[0].slice(0, 60);
		folderName = firstLine
			.toLowerCase()
			.replace(/[^a-z0-9\s-]/g, '')
			.replace(/\s+/g, '-')
			.replace(/-{2,}/g, '-')
			.trim()
			.replace(/^-+|-+$/g, '');
	}

	async function createProject() {
		if (!idea.trim()) { createError = 'Please enter an idea.'; return; }
		creatingProject = true;
		createError = '';
		try {
			const result = await api.newProject({
				idea,
				folder_name: folderName || undefined,
				project_dir: projectDir || undefined
			});
			project.set({ loaded: true, path: result.path, name: result.name, stage: result.stage as any });
			goto('/project');
		} catch (e: unknown) {
			createError = e instanceof Error ? e.message : String(e);
		} finally {
			creatingProject = false;
		}
	}

	// ── Open / Import existing directory ──────────────────────────────────
	let openPath = '';
	let scanning = false;
	let browsing = false;
	let scanResult: ScanResult | null = null;
	let scanError = '';
	let importProjectName = '';
	let importing = false;
	let importError = '';

	// Advanced import settings
	let showAdvanced = false;
	let importProjectDir = '';

	async function browse() {
		browsing = true;
		scanError = '';
		try {
			const result = await api.browseFolder();
			if (!result.cancelled && result.path) {
				openPath = result.path;
				// Auto-scan after picking
				await scanDirectory();
			}
		} catch (e: unknown) {
			scanError = e instanceof Error ? e.message : String(e);
		} finally {
			browsing = false;
		}
	}

	async function scanDirectory() {
		if (!openPath.trim()) { scanError = 'Enter a directory path.'; return; }
		scanning = true;
		scanResult = null;
		scanError = '';
		importError = '';
		try {
			scanResult = await api.scanDirectory(openPath.trim());
			if (scanResult.type === 'invalid') {
				scanError = scanResult.error ?? 'Directory not found';
				scanResult = null;
			} else {
				importProjectName = openPath.trim().split('/').pop()?.replace(/-/g, ' ') ?? '';
			}
		} catch (e: unknown) {
			scanError = e instanceof Error ? e.message : String(e);
		} finally {
			scanning = false;
		}
	}

	async function loadNovelWriterProject() {
		importing = true;
		importError = '';
		try {
			const result = await api.loadProject(openPath.trim());
			const state = await api.projectState();
			project.set(state);
			goto('/project');
		} catch (e: unknown) {
			importError = e instanceof Error ? e.message : String(e);
		} finally {
			importing = false;
		}
	}

	async function importGenericDirectory() {
		importing = true;
		importError = '';
		try {
			const result = await api.importProject({
				source_path: openPath.trim(),
				project_name: importProjectName || undefined,
				project_dir: importProjectDir || undefined
			});
			const state = await api.projectState();
			project.set(state);
			goto('/project');
		} catch (e: unknown) {
			importError = e instanceof Error ? e.message : String(e);
		} finally {
			importing = false;
		}
	}

	onMount(async () => {
		try {
			const s = await api.status();
			sysStatus.set(s);
		} catch {}
	});
</script>

<svelte:head>
	<title>NovelWriter UI — Start</title>
</svelte:head>

<PrereqBar />

<div class="max-w-5xl mx-auto px-5 py-10 space-y-8 animate-fade-in">

	<!-- Hero -->
	<div class="text-center space-y-2 pb-2">
		<h1 class="text-3xl font-bold text-ink-50 tracking-tight">
			Write your novel with AI.
		</h1>
		<p class="text-ink-500 text-sm max-w-md mx-auto">
			Powered by Ollama and running entirely on your machine.
		</p>
	</div>

	<!-- Two columns: New Novel | Open/Import -->
	<div class="grid grid-cols-1 md:grid-cols-2 gap-5">

		<!-- ── NEW NOVEL ──────────────────────────────────────────────────── -->
		<div class="card p-6 flex flex-col gap-4">
			<div class="flex items-center gap-2">
				<span class="text-2xl">✨</span>
				<div>
					<h2 class="text-base font-semibold text-ink-100">New Novel</h2>
					<p class="text-xs text-ink-500">Start from a blank idea</p>
				</div>
			</div>

			<div class="space-y-3 flex-1">
				<div>
					<label class="label" for="idea">Your idea</label>
					<textarea
						id="idea"
						class="textarea min-h-[120px]"
						placeholder="A sci-fi story about an AI that discovers it's been writing its own training data for years…"
						bind:value={idea}
					></textarea>
				</div>

				<div>
					<label class="label" for="folder">Project folder name</label>
					<input
						id="folder"
						class="input"
						placeholder="auto-generated from your idea"
						bind:value={folderName}
					/>
					<p class="text-[11px] text-ink-700 mt-1">
						Saved to ~/NovelWriter/{folderName || '<folder>'}
					</p>
				</div>
			</div>

			{#if createError}
				<p class="text-xs text-red-400 bg-red-950/30 border border-red-800/30 rounded-lg px-3 py-2">
					{createError}
				</p>
			{/if}

			<button
				class="btn-primary w-full justify-center"
				on:click={createProject}
				disabled={creatingProject || !idea.trim()}
			>
				{#if creatingProject}
					<span class="spinner w-4 h-4"></span>
					Creating…
				{:else}
					Create Novel →
				{/if}
			</button>
		</div>

		<!-- ── OPEN / IMPORT ───────────────────────────────────────────────── -->
		<div class="card p-6 flex flex-col gap-4">
			<div class="flex items-center gap-2">
				<span class="text-2xl">📂</span>
				<div>
					<h2 class="text-base font-semibold text-ink-100">Open Project</h2>
					<p class="text-xs text-ink-500">Load an existing project or import from files</p>
				</div>
			</div>

			<div class="space-y-3 flex-1">
				<div>
					<label class="label" for="open-path">Directory path</label>
					<div class="flex gap-2">
						<input
							id="open-path"
							class="input flex-1"
							placeholder="/Users/you/writing/my-novel"
							bind:value={openPath}
							on:keydown={(e) => e.key === 'Enter' && scanDirectory()}
						/>
						<button
							class="btn-secondary flex-shrink-0"
							on:click={browse}
							disabled={browsing || scanning}
							title="Open folder picker"
						>
							{#if browsing}
								<span class="spinner w-3.5 h-3.5"></span>
							{:else}
								📁
							{/if}
						</button>
						<button
							class="btn-secondary flex-shrink-0"
							on:click={scanDirectory}
							disabled={scanning || !openPath.trim()}
						>
							{#if scanning}
								<span class="spinner w-3.5 h-3.5"></span>
							{:else}
								Scan
							{/if}
						</button>
					</div>
					<p class="text-[11px] text-ink-700 mt-1">
						Click 📁 to pick a folder, or paste a path and hit Scan.
					</p>
				</div>

				<!-- Scan results -->
				{#if scanError}
					<p class="text-xs text-red-400 bg-red-950/30 border border-red-800/30 rounded-lg px-3 py-2">
						{scanError}
					</p>
				{/if}

				{#if scanResult}
					<div class="space-y-3 animate-fade-in">
						<!-- NovelWriter project -->
						{#if scanResult.type === 'novelwriter'}
							<div class="bg-violet-950/30 border border-violet-800/30 rounded-lg p-3 space-y-2">
								<p class="text-xs font-medium text-violet-400">✓ NovelWriter project detected</p>
								<div class="grid grid-cols-3 gap-2 text-[11px] text-ink-500">
									<span class="{scanResult.has_plot ? 'text-green-400' : 'text-ink-700'}">
										{scanResult.has_plot ? '✓' : '○'} plot.md
									</span>
									<span class="{scanResult.has_outline ? 'text-green-400' : 'text-ink-700'}">
										{scanResult.has_outline ? '✓' : '○'} outline
									</span>
									<span class="{scanResult.has_drafts ? 'text-green-400' : 'text-ink-700'}">
										{scanResult.has_drafts ? '✓' : '○'} drafts
									</span>
								</div>
								<button
									class="btn-primary w-full justify-center text-xs"
									on:click={loadNovelWriterProject}
									disabled={importing}
								>
									{#if importing}
										<span class="spinner w-3.5 h-3.5"></span>
										Loading…
									{:else}
										Open Project →
									{/if}
								</button>
							</div>

						<!-- Generic writing directory -->
						{:else if scanResult.type === 'generic'}
							<div class="bg-base-800 border border-border rounded-lg p-3 space-y-2.5">
								<p class="text-xs font-medium text-ink-300">Writing directory found</p>
								<div class="text-[11px] text-ink-500 space-y-0.5">
									<div>{scanResult.total_files} .md file(s) · {(scanResult.total_words ?? 0).toLocaleString()} words</div>
									{#if (scanResult.chapters?.length ?? 0) > 0}
										<div>{scanResult.chapters?.length} chapter folder(s)</div>
										{#each (scanResult.chapters ?? []).slice(0, 4) as ch}
											<div class="pl-2 text-ink-700">└ {ch.name} ({ch.files.length} files)</div>
										{/each}
										{#if (scanResult.chapters?.length ?? 0) > 4}
											<div class="pl-2 text-ink-700">└ …{(scanResult.chapters?.length ?? 0) - 4} more</div>
										{/if}
									{/if}
								</div>

								<div>
									<label class="label" for="import-name">Project name</label>
									<input
										id="import-name"
										class="input"
										placeholder="my-novel"
										bind:value={importProjectName}
									/>
								</div>

								<div class="flex gap-2">
									<button
										class="btn-primary flex-1 justify-center text-xs"
										on:click={importGenericDirectory}
										disabled={importing}
										title="Copy .md files into a new NovelWriter project and use AI to extract plot, characters, and world"
									>
										{#if importing}
											<span class="spinner w-3.5 h-3.5"></span>
											Importing…
										{:else}
											Import & Continue →
										{/if}
									</button>
								</div>
								<p class="text-[10px] text-ink-700 leading-tight">
									Copies your files into a new NovelWriter project.
									After importing, run "Analyse Content" to extract plot and characters using AI.
								</p>
							</div>

						{:else if scanResult.type === 'empty'}
							<p class="text-xs text-ink-500 italic">No .md files found in that directory.</p>
						{/if}
					</div>
				{/if}

				{#if importError}
					<p class="text-xs text-red-400 bg-red-950/30 border border-red-800/30 rounded-lg px-3 py-2">
						{importError}
					</p>
				{/if}
			</div>
		</div>

	</div>

	<!-- Feature highlights -->
	<div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
		{#each [
			{ icon: '🧠', title: 'Fully local', desc: 'Runs on your machine via Ollama. No data sent anywhere.' },
			{ icon: '📖', title: '70k–100k words', desc: 'Plot → Characters → Outline → Scene-by-scene writing.' },
			{ icon: '♻️', title: 'Import existing', desc: 'Bring in chapters and .md files and keep writing.' }
		] as feat}
			<div class="card p-4 flex gap-3">
				<span class="text-xl flex-shrink-0">{feat.icon}</span>
				<div>
					<p class="text-xs font-semibold text-ink-100">{feat.title}</p>
					<p class="text-[11px] text-ink-500 mt-0.5 leading-relaxed">{feat.desc}</p>
				</div>
			</div>
		{/each}
	</div>
</div>
