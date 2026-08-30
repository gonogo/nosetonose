<script lang="ts">
	import { countLabel } from '$lib/courses';
	import { peopleByRegion, peopleRegionAnchor } from '$lib/people';
	import type { Person } from '$lib/types';

	let {
		data
	}: {
		data: {
			sections: {
				id: string;
				heading: string;
				description: string;
				groupByRegion: boolean;
				people: Person[];
			}[];
		};
	} = $props();
</script>

<svelte:head>
	<title>Team — Nose to Nose</title>
</svelte:head>

<main class="site-main">
	<header>
		<h1>Team</h1>
		<p class="page-intro">
			Facilitators, associates, and people we remember. Names link through to a short biography and
			the courses they lead.
		</p>
	</header>

	<div class="layout-with-sidebar">
		<nav class="contents-sidebar" aria-label="Team sections">
			<h2>Jump to</h2>
			<ul>
				{#each data.sections as section}
					<li>
						<a href="#{section.id}">{section.heading} ({section.people.length})</a>
						{#if section.groupByRegion}
							<ul class="contents-sidebar-nested">
								{#each peopleByRegion(section.people) as group}
									<li>
										<a href="#{peopleRegionAnchor(section.id, group.region)}"
											>{group.region} ({group.people.length})</a
										>
									</li>
								{/each}
							</ul>
						{/if}
					</li>
				{/each}
			</ul>
		</nav>

		<div>
			{#each data.sections as section}
				<section class="contents-section" id={section.id}>
					<h2>{section.heading}</h2>
					<p class="meta">{section.description}</p>
					{#if section.groupByRegion}
						{#each peopleByRegion(section.people) as group}
							<div class="contents-subsection" id={peopleRegionAnchor(section.id, group.region)}>
								<h3>{group.region}</h3>
								<p class="subsection-count">{countLabel(group.people.length, 'person')}</p>
								<ul class="name-list">
									{#each group.people as person}
										<li>
											<a href="/team/{person.id}">{person.name}</a>
											{#if person.country}
												<span class="person-meta">{person.country}</span>
											{/if}
										</li>
									{/each}
								</ul>
							</div>
						{/each}
					{:else}
						<ul class="name-list">
							{#each section.people as person}
								<li>
									<a href="/team/{person.id}">{person.name}</a>
									{#if person.country}
										<span class="person-meta">{person.country}</span>
									{/if}
								</li>
							{/each}
						</ul>
					{/if}
				</section>
			{/each}
		</div>
	</div>
</main>
