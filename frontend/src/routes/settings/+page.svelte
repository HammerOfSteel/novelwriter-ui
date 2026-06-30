<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { settings } from '$lib/stores';
	import type { Settings, TestConnectionResult } from '$lib/api';

	let form: Partial<Settings> = {};
	let models: string[] = [];
	let loading = true;
	let saving = false;
	let saveSuccess = false;
	let error = '';
	let modelsError = '';

	// Test-connection state
	let testing = false;
	let testResult: TestConnectionResult | null = null;

	// Installing prereqs
	let installing = false;
	let installOutput = '';

	onMount(async () => {
		try {
			const [s, m] = await Promise.allSettled([api.getSettings(), api.models()]);
			if (s.status === 'fulfilled') {
				form = { ...s.value };
				settings.set(s.value);
			}
			if (m.status === 'fulfilled') {
				models = m.value.models;
			} else {
				modelsError = 'Could not reach the LLM backend.';
			}
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	});

	async function save() {
		saving = true;
		saveSuccess = false;
		error = '';
		try {
			const result = await api.saveSettings(form);
			settings.set(result.config);
			form = { ...result.config };
			saveSuccess = true;
			setTimeout(() => (saveSuccess = false), 3000);
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			saving = false;
		}
	}

	async function testConnection() {
		if (form.project_path) {
			try { await api.saveSettings(form); } catch { /* best-effort */ }
		}
		testing = true;
		testResult = null;
		try {
			testResult = await api.testConnection({
			BACKEND_TYPE: form.BACKEND_TYPE,
			OLLAMA_BASE_URL: form.OLLAMA_BASE_URL,
			API_URL: form.API_URL,
			API_KEY: form.API_KEY,
		});
			if (testResult.models.length > 0) {
				models = testResult.models;
				modelsError = '';
			}
		} catch (e: unknown) {
			testResult = {
				status: 'error',
				message: e instanceof Error ? e.message : String(e),
				models: []
			};
		} finally {
			testing = false;
		}
	}

	async function installDeps() {
		installing = true;
		installOutput = '';
		try {
			const res = await api.installPrereqs();
			installOutput = res.output;
		} catch (e: unknown) {
			installOutput = e instanceof Error ? e.message : String(e);
		} finally {
			installing = false;
		}
	}

	const THINK_MODES = ['off', 'low', 'medium', 'high'];

	// Persist debug mode to localStorage immediately on toggle — no project needed.
	$: {
		if (form.DEBUG_MODE !== undefined) {
			try { localStorage.setItem('debug_mode', form.DEBUG_MODE ? 'true' : 'false'); } catch {}
			settings.update((s) => s ? { ...s, DEBUG_MODE: form.DEBUG_MODE! } : s);
		}
	}
	const LANGUAGES = ['English', 'Japanese'];

	$: backendType = form.BACKEND_TYPE ?? 'ollama';

	function setBackend(type: 'ollama' | 'api') {
		form = { ...form, BACKEND_TYPE: type };
		testResult = null;
		models = [];
	}

	$: testDotClass =
		testResult?.status === 'ok'
			? 'bg-green-400'
			: testResult?.status === 'warn'
				? 'bg-amber-400'
				: testResult?.status === 'error'
					? 'bg-red-400'
					: 'bg-ink-700';
</script>

<svelte:head>
	<title>Settings — NovelWriter UI</title>
</svelte:head>

<div class="max-w-2xl mx-auto px-5 py-10 space-y-6 animate-fade-in">

	<div>
		<h1 class="text-xl font-bold text-ink-100">Settings</h1>
		<p class="text-xs text-ink-500 mt-1">
			Saved to <code class="font-mono text-ink-400">config_override.json</code> inside the active project.
			{#if form.project_path}
				<span class="text-ink-700 ml-1">({form.project_path})</span>
			{:else}
				<span class="text-amber-400 ml-1">— Load a project first to save settings.</span>
			{/if}
		</p>
	</div>

	{#if loading}
		<div class="text-ink-500 text-sm">Loading settings…</div>
	{:else}

		<!-- LLM BACKEND -->
		<section class="card p-5 space-y-5">
			<h2 class="text-sm font-semibold text-ink-300 border-b border-border pb-2">LLM Backend</h2>

			<!-- Toggle -->
			<div class="flex gap-2">
				<button
					type="button"
					class="px-4 py-2 rounded-lg text-xs font-medium transition-colors
					{backendType === 'ollama'
						? 'bg-violet-600 text-white'
						: 'bg-base-800 text-ink-400 hover:text-ink-200 hover:bg-base-700'}"
					on:click={() => setBackend('ollama')}
				>
					Ollama
				</button>
				<button
					type="button"
					class="px-4 py-2 rounded-lg text-xs font-medium transition-colors
					{backendType === 'api'
						? 'bg-violet-600 text-white'
						: 'bg-base-800 text-ink-400 hover:text-ink-200 hover:bg-base-700'}"
					on:click={() => setBackend('api')}
				>
					API <span class="opacity-60 text-[10px]">(OpenAI-compatible)</span>
				</button>
			</div>

			{#if backendType === 'ollama'}
				<div class="space-y-4">
					<div>
						<label class="label" for="base-url">Ollama Base URL</label>
						<input id="base-url" class="input" bind:value={form.OLLAMA_BASE_URL}
							placeholder="http://localhost:11434" />
					</div>

					<div>
						<label class="label" for="model">Model</label>
						{#if models.length > 0}
							<select id="model" class="input" bind:value={form.DEFAULT_MODEL}>
								<option value="">— choose a model —</option>
								{#each models as m}
									<option value={m}>{m}</option>
								{/each}
							</select>
						{:else}
							<input id="model" class="input" bind:value={form.DEFAULT_MODEL}
								placeholder="e.g. llama3.2:latest" />
							{#if modelsError}
								<p class="text-[11px] text-amber-400 mt-1">{modelsError}</p>
							{/if}
						{/if}
					</div>

					<div class="grid grid-cols-2 gap-4">
						<div>
							<label class="label" for="ctx-len">Context length (tokens)</label>
							<input id="ctx-len" type="number" class="input"
								bind:value={form.CONTEXT_LENGTH_SIZE} min="1024" step="1024" />
						</div>
						<div>
							<label class="label" for="think">Think mode</label>
							<select id="think" class="input" bind:value={form.THINK_MODE}>
								{#each THINK_MODES as m}
									<option value={m}>{m}</option>
								{/each}
							</select>
						</div>
					</div>

					<div class="pt-1 border-t border-border">
						<p class="text-[11px] text-ink-500 mb-2">
							Ollama must be installed and running locally.
							<a href="https://ollama.com/download" target="_blank" rel="noopener"
								class="text-violet-400 hover:underline">ollama.com/download ↗</a>
						</p>
						<button type="button" class="btn-secondary text-xs"
							on:click={installDeps} disabled={installing}>
							{#if installing}
								<span class="spinner w-3 h-3 mr-1.5"></span>Installing…
							{:else}
								Install / repair Python deps
							{/if}
						</button>
						{#if installOutput}
							<pre class="mt-2 text-[10px] text-ink-400 bg-base-950 rounded p-2 max-h-32 overflow-auto whitespace-pre-wrap">{installOutput}</pre>
						{/if}
					</div>
				</div>

			{:else}
				<div class="space-y-4">
					<p class="text-[11px] text-ink-500">
						Works with <strong class="text-ink-300">LM Studio</strong>,
						<strong class="text-ink-300">Jan</strong>,
						<strong class="text-ink-300">text-generation-webui</strong>,
						and any server exposing an OpenAI-compatible
						<code class="font-mono text-ink-400">/v1/chat/completions</code> endpoint.
					</p>

					<div>
						<label class="label" for="api-url">API URL</label>
						<input id="api-url" class="input" bind:value={form.API_URL}
							placeholder="http://127.0.0.1:1234" />
						<p class="text-[11px] text-ink-700 mt-1">
							LM Studio default: <code class="font-mono">http://127.0.0.1:1234</code>
						</p>
					</div>

					<div>
						<label class="label" for="api-model">Model ID</label>
						{#if models.length > 0}
							<select id="api-model" class="input" bind:value={form.API_MODEL}>
								<option value="">— choose a model —</option>
								{#each models as m}
									<option value={m}>{m}</option>
								{/each}
							</select>
						{:else}
							<input id="api-model" class="input" bind:value={form.API_MODEL}
								placeholder="e.g. lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF" />
							{#if modelsError}
								<p class="text-[11px] text-amber-400 mt-1">{modelsError}</p>
							{/if}
						{/if}
						<p class="text-[11px] text-ink-700 mt-1">
							Use <strong>Test Connection</strong> to auto-populate from the running server.
						</p>
					</div>

					<div>
						<label class="label" for="api-key">API Key</label>
						<input id="api-key" type="password" class="input"
							bind:value={form.API_KEY}
							placeholder="Leave empty if not required (LM Studio default)"
							autocomplete="off" />
					</div>
				</div>
			{/if}

			<!-- Test Connection -->
			<div class="flex items-start gap-4 pt-2 border-t border-border">
				<button type="button"
					class="btn-primary flex items-center gap-2 shrink-0"
					on:click={testConnection} disabled={testing}>
					{#if testing}
						<span class="spinner w-4 h-4"></span>Testing…
					{:else}
						<span class="w-2.5 h-2.5 rounded-full transition-colors {testDotClass}"></span>
						Test Connection
					{/if}
				</button>

				{#if testResult}
					<p class="text-xs mt-1.5 leading-relaxed
						{testResult.status === 'ok'
							? 'text-green-400'
							: testResult.status === 'warn'
								? 'text-amber-400'
								: 'text-red-400'}">
						{testResult.message}
					</p>
				{/if}
			</div>
		</section>

		<!-- NOVEL -->
		<section class="card p-5 space-y-4">
			<h2 class="text-sm font-semibold text-ink-300 border-b border-border pb-2">Novel</h2>

			<div>
				<label class="label" for="language">Output language</label>
				<select id="language" class="input" bind:value={form.NOVEL_LANGUAGE}>
					{#each LANGUAGES as l}
						<option value={l}>{l}</option>
					{/each}
				</select>
				<p class="text-[11px] text-ink-700 mt-1">
					English uses custom prompts; Japanese uses the original NovelWriter prompts.
				</p>
			</div>

			<div>
				<label class="label" for="viewpoint">Narrative viewpoint</label>
				<input id="viewpoint" class="input" bind:value={form.NOVEL_VIEWPOINT}
					placeholder="Third person omniscient" />
			</div>

			<div>
				<label class="label" for="style">Writing style</label>
				<input id="style" class="input" bind:value={form.NOVEL_STYLE}
					placeholder="Literary fiction / Light novel / Horror / etc." />
			</div>

			<div>
				<label class="label" for="max-ctx">Max context chars (per prompt)</label>
				<input id="max-ctx" type="number" class="input"
					bind:value={form.MAX_CONTEXT_CHARS} min="500" step="500" />
			</div>
		</section>

		<!-- DEVELOPER / DEBUG -->
		<section class="card p-5 space-y-4">
			<h2 class="text-sm font-semibold text-ink-300 border-b border-border pb-2">Developer</h2>

			<label class="flex items-center gap-3 cursor-pointer select-none">
				<span class="relative inline-flex h-5 w-9 shrink-0">
					<input
						id="debug-mode"
						type="checkbox"
						class="peer sr-only"
						bind:checked={form.DEBUG_MODE}
					/>
					<!-- track -->
					<span class="absolute inset-0 rounded-full bg-base-700 transition-colors
						peer-checked:bg-violet-600"></span>
					<!-- thumb -->
					<span class="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-ink-200 shadow
						transition-transform peer-checked:translate-x-4"></span>
				</span>
				<span class="text-sm text-ink-300">Debug mode</span>
			</label>
			<p class="text-[11px] text-ink-600 -mt-2 pl-12">
				When on, the backend emits verbose trace logs to the uvicorn console and the
				frontend logs all API calls and store state to the browser DevTools console.
				A live state panel also appears on the Project page.
			</p>
		</section>

		{#if error}
			<p class="text-xs text-red-400 bg-red-950/30 border border-red-800/30 rounded-lg px-3 py-2">
				{error}
			</p>
		{/if}

		<div class="flex items-center gap-3">
			<button class="btn-primary" on:click={save}
				disabled={saving || !form.project_path}>
				{#if saving}
					<span class="spinner w-4 h-4"></span>Saving…
				{:else}
					Save Settings
				{/if}
			</button>

			{#if saveSuccess}
				<span class="text-xs text-green-400 animate-fade-in">✓ Saved</span>
			{/if}

			{#if !form.project_path}
				<span class="text-xs text-amber-400">No project loaded — open a project to save.</span>
			{/if}
		</div>

	{/if}
</div>
