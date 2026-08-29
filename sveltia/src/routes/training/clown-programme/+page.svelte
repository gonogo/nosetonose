<script lang="ts">
	import EditorialPage from '$lib/components/EditorialPage.svelte';
	let { data } = $props();
</script>

<EditorialPage {data} crumbHref="/training" crumbLabel="Training" />
