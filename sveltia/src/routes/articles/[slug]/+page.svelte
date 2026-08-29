<script lang="ts">
	import Markdown from '$lib/components/Markdown.svelte';
	import type { Article } from '$lib/types';

	let { data }: { data: Article } = $props();
</script>

<svelte:head>
	<title>{data.title} — Nose to Nose</title>
</svelte:head>

<main class="site-main narrow">
	<p class="crumb"><a href="/articles">Articles</a></p>
	<article>
		<Markdown source={data.body} />
		{#if data.source_url}
			<p class="meta">Original page: <a href={data.source_url}>{data.source_url}</a></p>
		{/if}
	</article>
</main>
