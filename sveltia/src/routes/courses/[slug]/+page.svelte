<script lang="ts">
	import Markdown from '$lib/components/Markdown.svelte';
	import { formatDateRange } from '$lib/courses';
	import { firstParagraph } from '$lib/people';
	import type { Course, Person, Venue } from '$lib/types';

	let {
		data
	}: {
		data: { course: Course; venue: Venue | null; facilitators: Person[] };
	} = $props();

	const { course, venue, facilitators } = $derived(data);

	const rows = $derived(
		[
			['Dates', formatDateRange(course.start_date, course.end_date)],
			['Region', course.region],
			['Country', course.location_country],
			['Venue', venue?.name],
			['Location', venue?.location],
			['Language', course.language],
			['Level', course.clown_level],
			['Medium', course.medium],
			['Group size', course.maximum_group_size ? String(course.maximum_group_size) : null],
			['Fee', course.course_fee],
			['Deposit', course.course_fee_deposit],
			['Prerequisites', course.prerequisites]
		].filter((row): row is [string, string] => Boolean(row[1]))
	);
</script>

<svelte:head>
	<title>{course.title} — Nose to Nose</title>
</svelte:head>

<main class="site-main narrow">
	<p class="crumb"><a href="/courses">Courses</a></p>
	<p class="type-label">{course.clown_level || course.medium}</p>
	<h1>{course.title}</h1>

	<dl class="details-list">
		{#each rows as [label, value]}
			<dt>{label}</dt>
			<dd>{value}</dd>
		{/each}
		{#if facilitators.length}
			<dt>Facilitators</dt>
			<dd>
				{#each facilitators as person, i}
					{i > 0 ? ', ' : ''}<a href="/team/{person.id}">{person.name}</a>
				{/each}
			</dd>
		{/if}
		{#if venue?.email}
			<dt>Venue email</dt>
			<dd><a href="mailto:{venue.email}">{venue.email}</a></dd>
		{/if}
		{#if venue?.phone}
			<dt>Venue phone</dt>
			<dd>{venue.phone}</dd>
		{/if}
		{#if venue?.address}
			<dt>Address</dt>
			<dd>{venue.address}</dd>
		{/if}
	</dl>

	{#if course.course_description}
		<section>
			<h2>Course description</h2>
			<Markdown source={course.course_description} />
		</section>
	{/if}

	{#if course.schedule}
		<section>
			<h2>Schedule</h2>
			<Markdown source={course.schedule} />
		</section>
	{/if}

	{#if course.accommodation_and_meals}
		<section>
			<h2>Accommodation and meals</h2>
			<Markdown source={course.accommodation_and_meals} />
		</section>
	{/if}

	{#if facilitators.length}
		<section class="course-facilitators">
			<h2>Facilitators</h2>
			{#each facilitators as person (person.id)}
				{@const intro = firstParagraph(person.background)}
				<article class="person-hero course-facilitator">
					{#if person.photo}
						<img src={person.photo} alt="" />
					{:else}
						<div class="photo-fallback">No photo</div>
					{/if}
					<div>
						<h3><a href="/team/{person.id}">{person.name}</a></h3>
						{#if intro}
							<div class="prose facilitator-intro">
								<Markdown source={intro} />
							</div>
						{/if}
					</div>
				</article>
			{/each}
		</section>
	{/if}

	<p class="meta">
		<a href="/how-to-book">How to book</a>
		{#if course.source_url}
			· <a href={course.source_url}>Original listing</a>
		{/if}
	</p>
</main>
