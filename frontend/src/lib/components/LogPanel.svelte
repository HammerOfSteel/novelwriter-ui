<script lang="ts">
	import { jobLogs, jobStatus, logPanelOpen, clearLogs, isJobRunning } from '$lib/stores';
	import { afterUpdate, tick } from 'svelte';

	let logContainer: HTMLDivElement;
	let autoScroll = true;

	afterUpdate(async () => {
		if (autoScroll && logContainer) {
			await tick();
			logContainer.scrollTop = logContainer.scrollHeight;
		}
	});

	function onScroll() {
		if (!logContainer) return;
		const { scrollTop, scrollHeight, clientHeight } = logContainer;
		autoScroll = scrollHeight - scrollTop - clientHeight < 40;
	}
</script>

<div class="card flex flex-col overflow-hidden" style="min-height: 180px; max-height: 320px;">
	<!-- Header bar -->
	<div class="flex items-center justify-between px-4 py-2 bg-base-800 border-b border-border">
		<div class="flex items-center gap-2">
			<button
				class="text-xs text-ink-300 hover:text-ink-100 transition-colors font-medium"
				on:click={() => logPanelOpen.update((v) => !v)}
			>
				{$logPanelOpen ? '▾' : '▸'} Live Log
			</button>

			{#if $isJobRunning}
				<span class="flex items-center gap-1.5 text-xs text-violet-400">
					<span class="spinner w-3 h-3"></span>
					{$jobStatus.job_name ?? 'running…'}
				</span>
			{:else if $jobStatus.status === 'done'}
				<span class="text-xs text-green-400">✓ Done</span>
			{:else if $jobStatus.status === 'error'}
				<span class="text-xs text-red-400">✗ Error</span>
			{/if}
		</div>

		<div class="flex items-center gap-2">
			<label class="flex items-center gap-1.5 text-[11px] text-ink-500 cursor-pointer">
				<input type="checkbox" bind:checked={autoScroll} class="w-3 h-3 accent-violet-600" />
				auto-scroll
			</label>
			<button class="text-[11px] text-ink-500 hover:text-ink-300 transition-colors" on:click={clearLogs}>
				clear
			</button>
		</div>
	</div>

	<!-- Log content -->
	{#if $logPanelOpen}
		<div
			bind:this={logContainer}
			on:scroll={onScroll}
			class="flex-1 overflow-y-auto p-3 space-y-0.5 font-mono bg-base-950"
		>
			{#if $jobLogs.length === 0}
				<p class="text-ink-700 text-xs italic">Logs will appear here when a job starts…</p>
			{:else}
				{#each $jobLogs as entry}
					{#if entry.type === 'log'}
						<div class="log-line">{entry.message}</div>
					{:else if entry.type === 'done'}
						<div class="log-line done">✓ {entry.message}</div>
					{:else if entry.type === 'error'}
						<div class="log-line error">✗ {entry.message}</div>
					{/if}
				{/each}
			{/if}
		</div>
	{/if}
</div>
