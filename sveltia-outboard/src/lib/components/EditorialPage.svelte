<script lang="ts">
	import Markdown from '$lib/components/Markdown.svelte';

	let {
		data,
		crumbHref,
		crumbLabel
	}: {
		data: { title: string; body: string; documentTitle?: string };
		crumbHref?: string;
		crumbLabel?: string;
	} = $props();
</script>

<svelte:head>
	<title>{data.documentTitle || data.title} — Nose to Nose</title>
</svelte:head>

<main class="site-main narrow">
	{#if crumbHref && crumbLabel}
		<p class="crumb"><a href={crumbHref}>{crumbLabel}</a></p>
	{/if}
	<article>
		<Markdown source={data.body} />
	</article>
</main>
