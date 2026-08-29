<script lang="ts">
	import { page } from '$app/state';

	let { children } = $props();
	const path = $derived(page.url.pathname);
</script>

<nav class="training-subnav" aria-label="Training sections">
	<a
		href="/training/clown-programme"
		aria-current={path.startsWith('/training/clown-programme') ? 'page' : undefined}
		>Clown programme</a
	>
	<a
		href="/training/for-organisations"
		aria-current={path.startsWith('/training/for-organisations') ? 'page' : undefined}
		>For organisations</a
	>
</nav>

{@render children()}
