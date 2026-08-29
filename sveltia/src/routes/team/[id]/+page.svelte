<script lang="ts">
	import Markdown from '$lib/components/Markdown.svelte';
	import { courseSlug, formatDateRange } from '$lib/courses';
	import { personDisplayLabel, stripLeadingImages } from '$lib/people';
	import type { Course, Person } from '$lib/types';

	let { data }: { data: { person: Person; courses: Course[] } } = $props();
	const person = $derived(data.person);
	const bio = $derived(stripLeadingImages(person.background));
</script>

<svelte:head>
	<title>{person.name} — Nose to Nose</title>
</svelte:head>

<main class="site-main narrow">
	<p class="crumb"><a href="/team">Team</a></p>
	<p class="type-label">{personDisplayLabel(person)}</p>
	<div class="person-hero">
		{#if person.photo}
			<img src={person.photo} alt="" />
		{:else}
			<div class="photo-fallback">No photo</div>
		{/if}
		<div>
			<h1>{person.name}</h1>
			<dl class="details-list">
				{#if person.country}
					<dt>Country</dt>
					<dd>{person.country}</dd>
				{/if}
				{#if person.region}
					<dt>Region</dt>
					<dd>{person.region}</dd>
				{/if}
			</dl>
		</div>
	</div>

	<section>
		<h2>Background</h2>
		{#if bio}
			<Markdown source={bio} />
		{:else}
			<p class="unavailable">No biography available.</p>
		{/if}
	</section>

	{#if data.courses.length}
		<section>
			<h2>Courses</h2>
			<ul class="course-list">
				{#each data.courses as course}
					<li>
						<a href="/courses/{courseSlug(course.id)}">{course.title}</a>
						<p>{formatDateRange(course.start_date, course.end_date)}</p>
					</li>
				{/each}
			</ul>
		</section>
	{/if}
</main>
