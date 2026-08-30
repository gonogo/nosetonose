<script lang="ts">
	import { page } from '$app/state';

	const status = $derived(page.status);
	const message = $derived(page.error?.message ?? 'Something went wrong');
</script>

<svelte:head>
	<title>{status} — Nose to Nose</title>
</svelte:head>

<main class="site-main narrow">
	<h1>{status}</h1>
	<p class="page-intro">{message}</p>
	<p><a href="/">Back to home</a></p>
</main>
