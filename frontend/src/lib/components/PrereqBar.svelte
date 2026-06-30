<script lang="ts">
	import { sysStatus } from '$lib/stores';
	import { api } from '$lib/api';

	let installing = false;
	let installError = '';

	async function install() {
		installing = true;
		installError = '';
		try {
			await api.installPrereqs();
			const s = await api.status();
			sysStatus.set(s);
		} catch (e: unknown) {
			installError = e instanceof Error ? e.message : String(e);
		} finally {
			installing = false;
		}
	}
</script>

{#if $sysStatus}
	<div class="flex items-center gap-3 px-4 py-2 bg-base-900 border-b border-border text-xs">
		<!-- Ollama status -->
		<span class="flex items-center gap-1.5">
			<span
				class="w-2 h-2 rounded-full {$sysStatus.ollama ? 'bg-green-400' : 'bg-red-500'}"
			></span>
			<span class="text-ink-300">Ollama</span>
			{#if !$sysStatus.ollama}
				<span class="text-red-400 ml-1">not found — is it running?</span>
			{/if}
		</span>

		<span class="text-ink-700">·</span>

		<!-- Deps status -->
		<span class="flex items-center gap-1.5">
			<span
				class="w-2 h-2 rounded-full {$sysStatus.deps ? 'bg-green-400' : 'bg-amber-400'}"
			></span>
			<span class="text-ink-300">Python deps</span>
			{#if !$sysStatus.deps}
				<button
					class="ml-2 btn-primary py-0.5 text-xs"
					on:click={install}
					disabled={installing}
				>
					{#if installing}
						<span class="spinner w-3 h-3"></span>
					{/if}
					Install
				</button>
			{/if}
		</span>

		{#if installError}
			<span class="text-red-400 ml-2 truncate max-w-xs">{installError}</span>
		{/if}
	</div>
{/if}
