<script lang="ts">
	export let stage: string | null = null;

	const STAGES = [
		{ key: 'init',     label: 'Init',    desc: 'Plot · Characters · World' },
		{ key: 'outline',  label: 'Outline', desc: 'Chapter & scene structure' },
		{ key: 'write',    label: 'Write',   desc: 'Scene-by-scene drafting' },
		{ key: 'done',     label: 'Done',    desc: 'Novel complete' }
	];

	function stageIndex(s: string | null): number {
		if (s === 'imported') return 0;
		const idx = STAGES.findIndex((st) => st.key === s);
		return idx === -1 ? 0 : idx;
	}

	$: currentIdx = stageIndex(stage);
</script>

<div class="flex flex-col gap-1">
	{#each STAGES as st, i}
		{@const done = i < currentIdx}
		{@const active = i === currentIdx}
		<div class="flex items-start gap-3 py-1.5 relative">
			<!-- Connector line -->
			{#if i < STAGES.length - 1}
				<div
					class="absolute left-3 top-6 w-px h-full {done ? 'bg-violet-600' : 'bg-border'}"
				></div>
			{/if}

			<!-- Dot -->
			<div
				class="relative z-10 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs
				{done
					? 'bg-violet-600 text-white'
					: active
					? 'bg-violet-600/20 border-2 border-violet-500 text-violet-400'
					: 'bg-base-800 border border-border text-ink-700'}"
			>
				{#if done}
					✓
				{:else if active}
					<span class="w-2 h-2 rounded-full bg-violet-500 animate-pulse-slow"></span>
				{:else}
					{i + 1}
				{/if}
			</div>

			<!-- Label -->
			<div>
				<div class="text-xs font-medium {active ? 'text-ink-100' : done ? 'text-ink-300' : 'text-ink-700'}">
					{st.label}
				</div>
				{#if active}
					<div class="text-[11px] text-ink-500 leading-tight">{st.desc}</div>
				{/if}
			</div>
		</div>
	{/each}
</div>
