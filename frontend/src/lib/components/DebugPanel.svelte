<script lang="ts">
	import { project, jobStatus, isJobRunning, debugMode } from '$lib/stores';

	// Keep a live copy of the stores for display.
	$: _project = $project;
	$: _jobStatus = $jobStatus;
	$: _isJobRunning = $isJobRunning;

	let open = false;
</script>

{#if $debugMode}
	<div class="fixed bottom-4 right-4 z-50 w-80 font-mono text-[10px]">
		<button
			type="button"
			class="w-full flex items-center justify-between px-3 py-1.5 rounded-t-lg bg-violet-900/80 text-violet-200 border border-violet-700/60 backdrop-blur"
			on:click={() => (open = !open)}
		>
			<span>🐛 Debug panel</span>
			<span class="opacity-60">{open ? '▲' : '▼'}</span>
		</button>

		{#if open}
			<div class="bg-base-950/95 border border-violet-700/40 border-t-0 rounded-b-lg p-3
				space-y-2 backdrop-blur max-h-72 overflow-y-auto">

				<div>
					<p class="text-violet-400 font-semibold mb-1">jobStatus</p>
					<pre class="text-ink-300 whitespace-pre-wrap break-all">{JSON.stringify(_jobStatus, null, 2)}</pre>
				</div>

				<div>
					<p class="text-violet-400 font-semibold mb-1">isJobRunning</p>
					<pre class="text-ink-300">{_isJobRunning}</pre>
				</div>

				<div>
					<p class="text-violet-400 font-semibold mb-1">project</p>
					<pre class="text-ink-300 whitespace-pre-wrap break-all">{JSON.stringify({
						loaded: _project.loaded,
						name: _project.name,
						stage: _project.stage,
						path: _project.path,
						is_imported: _project.is_imported,
						total_scenes: _project.total_scenes,
						written_scenes: _project.written_scenes,
					}, null, 2)}</pre>
				</div>
			</div>
		{/if}
	</div>
{/if}
