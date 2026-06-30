<script lang="ts">
	import type { ProjectSummary } from '$lib/api';
	export let project: ProjectSummary;
	export let selected = false;
	export let jobRunning = false; // job is currently running on this project

	const STAGE_LABELS: Record<string, string> = {
		init:     'Setting up',
		outline:  'Outlining',
		write:    'Writing',
		done:     'Complete',
		imported: 'Ready to analyse',
	};
	const STAGE_COLORS: Record<string, string> = {
		init:     'text-ink-500 bg-base-800',
		outline:  'text-blue-400 bg-blue-950/40',
		write:    'text-violet-400 bg-violet-950/40',
		done:     'text-green-400 bg-green-950/40',
		imported: 'text-amber-400 bg-amber-950/40',
	};

	$: label = STAGE_LABELS[project.stage] ?? project.stage;
	$: badgeClass = STAGE_COLORS[project.stage] ?? STAGE_COLORS.init;
	$: pct = project.total_scenes > 0
		? Math.round((project.written_scenes / project.total_scenes) * 100)
		: 0;
</script>

<button
	type="button"
	class="w-full text-left rounded-xl border transition-all duration-150 p-4 space-y-2 focus:outline-none
		{selected
			? 'border-violet-500 bg-violet-950/20 shadow-sm shadow-violet-900/20'
			: 'border-border bg-base-900 hover:border-border hover:bg-base-800/60'}"
	on:click
>
	<!-- Name row -->
	<div class="flex items-start justify-between gap-2">
		<span class="text-sm font-semibold text-ink-100 leading-tight line-clamp-2 flex-1">
			{project.name.replace(/-/g, ' ')}
		</span>

		<!-- Running indicator -->
		{#if jobRunning}
			<span class="flex-shrink-0 flex items-center gap-1 text-[10px] text-violet-400 font-medium">
				<span class="spinner w-3 h-3"></span>
				running
			</span>
		{/if}
	</div>

	<!-- Stage badge -->
	<div class="flex items-center gap-2">
		<span class="px-2 py-0.5 rounded-full text-[10px] font-medium {badgeClass}">
			{label}
		</span>
		{#if project.is_imported}
			<span class="px-2 py-0.5 rounded-full text-[10px] font-medium text-ink-600 bg-base-800">
				imported
			</span>
		{/if}
	</div>

	<!-- Progress bar (only for write stage) -->
	{#if project.stage === 'write' && project.total_scenes > 0}
		<div class="space-y-1">
			<div class="h-1 w-full rounded-full bg-base-700 overflow-hidden">
				<div
					class="h-full rounded-full transition-all duration-500
					{jobRunning ? 'bg-violet-500 animate-pulse' : 'bg-violet-600'}"
					style="width: {pct}%"
				></div>
			</div>
			<p class="text-[10px] text-ink-600">
				{project.written_scenes} / {project.total_scenes} scenes
				{#if pct > 0}({pct}%){/if}
			</p>
		</div>
	{/if}

	<!-- Done check -->
	{#if project.stage === 'done'}
		<p class="text-[11px] text-green-500">✓ Novel complete</p>
	{/if}
</button>
