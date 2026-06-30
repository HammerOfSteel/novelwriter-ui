<script lang="ts">
	import type { Chapter } from '$lib/api';

	export let outline: Chapter[] = [];
	export let projectPath: string = '';

	function sceneFile(sceneId: number): string {
		return `${projectPath}/drafts/scene_${sceneId}.md`;
	}

	async function openFile(path: string) {
		try {
			await fetch(`/api/open?path=${encodeURIComponent(path)}`, { method: 'POST' });
		} catch {
			// Silently ignore — open-in-OS is best-effort
		}
	}

	function isWritten(sceneId: number): boolean {
		// Optimistic: the parent page passes in the full outline with scene status
		return false; // Overridden by parent via the `writtenSceneIds` prop
	}

	export let writtenSceneIds: Set<number> = new Set();
</script>

<div class="space-y-4">
	{#if outline.length === 0}
		<p class="text-ink-500 text-sm italic">No outline yet. Generate one to see the structure here.</p>
	{:else}
		{#each outline as chapter}
			<div class="card overflow-hidden">
				<!-- Chapter header -->
				<div class="px-4 py-2.5 bg-base-800 border-b border-border flex items-center gap-2">
					<span class="text-[10px] font-mono text-violet-400 uppercase tracking-widest">
						Chapter {chapter.chapter_id}
					</span>
					<span class="text-sm font-semibold text-ink-100 truncate">
						{chapter.chapter_title}
					</span>
				</div>

				<!-- Scenes grid -->
				<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-px bg-border">
					{#each chapter.scenes as scene}
						{@const written = writtenSceneIds.has(scene.scene_id)}
						<button
							class="group bg-base-900 hover:bg-base-800 transition-colors text-left p-3 flex flex-col gap-1.5
							       {written ? 'cursor-pointer' : 'cursor-default'}"
							on:click={() => written && openFile(sceneFile(scene.scene_id))}
							title={scene.summary ?? ''}
						>
							<div class="flex items-center justify-between">
								<span class="text-[10px] font-mono text-ink-500">#{scene.scene_id}</span>
								<span
									class="text-[10px] px-1.5 py-0.5 rounded-full font-medium
									{written
										? 'bg-green-500/15 text-green-400'
										: 'bg-base-800 text-ink-700 border border-border'}"
								>
									{written ? 'written' : 'pending'}
								</span>
							</div>
							<div class="text-xs text-ink-300 truncate leading-snug">
								{scene.title || scene.summary?.slice(0, 50) || '—'}
							</div>
							{#if written}
								<div class="text-[10px] text-violet-400 opacity-0 group-hover:opacity-100 transition-opacity">
									Open file ↗
								</div>
							{/if}
						</button>
					{/each}
				</div>
			</div>
		{/each}
	{/if}
</div>
