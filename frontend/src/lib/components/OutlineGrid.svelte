<script lang="ts">
	import type { Chapter } from '$lib/api';

	export let outline: Chapter[] = [];
	export let projectPath: string = '';
	export let writtenSceneIds: Set<number> = new Set();
	export let jobRunning: boolean = false;

	/** Called when the user clicks ↺ Regen on a scene. */
	export let onRegenScene: ((id: number) => void) | null = null;
	/** Called when the user clicks 🗑 Delete on a scene. */
	export let onDeleteScene: ((id: number) => void) | null = null;

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
						<div class="group bg-base-900 hover:bg-base-800 transition-colors p-3 flex flex-col gap-1.5">

							<!-- Top row: scene id + status badge -->
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

							<!-- Scene title / summary -->
							<button
								class="text-xs text-ink-300 truncate leading-snug text-left w-full
								       {written ? 'cursor-pointer hover:text-violet-300' : 'cursor-default'}"
								on:click={() => written && openFile(sceneFile(scene.scene_id))}
								title={scene.summary ?? ''}
							>
								{scene.title || scene.summary?.slice(0, 50) || '—'}
							</button>

							<!-- Action row — only visible on hover -->
							<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity mt-auto pt-1">
								{#if written}
									<button
										class="text-[10px] text-violet-400 hover:text-violet-300 flex-1 text-left"
										on:click={() => openFile(sceneFile(scene.scene_id))}
										title="Open file">
										Open ↗
									</button>
								{/if}
								<button
									class="text-[10px] px-1.5 py-0.5 rounded bg-violet-900/30 text-violet-400
									       hover:bg-violet-800/40 hover:text-violet-200 disabled:opacity-30 disabled:cursor-not-allowed"
									disabled={jobRunning}
									on:click={() => onRegenScene?.(scene.scene_id)}
									title={written ? 'Regenerate this scene' : 'Write this scene now'}>
									{written ? '↺' : '▶'}
								</button>
								{#if written}
									<button
										class="text-[10px] px-1.5 py-0.5 rounded bg-red-900/30 text-red-400
										       hover:bg-red-800/40 hover:text-red-300 disabled:opacity-30 disabled:cursor-not-allowed"
										disabled={jobRunning}
										on:click={() => onDeleteScene?.(scene.scene_id)}
										title="Delete this scene (mark as pending)">
										🗑
									</button>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/each}
	{/if}
</div>
