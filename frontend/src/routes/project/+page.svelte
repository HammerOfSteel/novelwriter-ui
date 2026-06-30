<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	// The /project route is retired — all project management is now in /books.
	onMount(() => goto('/books', { replaceState: true }));
</script>

<div class="flex items-center justify-center h-64 text-ink-500 text-sm">
	Redirecting to Books…
</div>
