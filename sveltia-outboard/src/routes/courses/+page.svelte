<script lang="ts">
	import {
		countLabel,
		courseGroupSummary,
		courseInstancePlace,
		courseSlug,
		coursesByCourseTitle,
		coursesByLevel,
		coursesByRegion,
		formatDateRange,
		levelSummary,
		regionAnchor,
		regionLevelAnchor
	} from '$lib/courses';
	import type { Course } from '$lib/types';

	let { data }: { data: { courses: Course[] } } = $props();
	const grouped = $derived(coursesByRegion(data.courses));
</script>

<svelte:head>
	<title>Courses — Nose to Nose</title>
</svelte:head>

<main class="site-main">
	<header>
		<h1>Courses</h1>
		<p class="page-intro">
			Upcoming workshops grouped by region and level. Small groups, in person and online.
		</p>
	</header>

	<div class="layout-with-sidebar">
		<nav class="contents-sidebar" aria-label="Regions and levels">
			<h2>Jump to</h2>
			<ul>
				{#each grouped as group}
					<li>
						<a class="contents-sidebar-region" href="#{regionAnchor(group.region)}"
							>{group.region} ({group.courses.length})</a
						>
						<ul class="contents-sidebar-nested">
							{#each coursesByLevel(group.courses) as levelGroup}
								<li>
									<a href="#{regionLevelAnchor(group.region, levelGroup.level)}"
										>{levelGroup.level} ({levelGroup.courses.length})</a
									>
								</li>
							{/each}
						</ul>
					</li>
				{/each}
			</ul>
		</nav>

		<div>
			{#each grouped as group}
				<section class="contents-section" id={regionAnchor(group.region)}>
					<h2>{group.region}</h2>
					<p class="meta">{countLabel(group.courses.length, 'course')}</p>
					{#each coursesByLevel(group.courses) as levelGroup}
						{@const summary = levelSummary(levelGroup.level)}
						<div
							class="contents-subsection"
							id={regionLevelAnchor(group.region, levelGroup.level)}
						>
							<div class="level-banner">
								<h3>{levelGroup.level}</h3>
								{#if summary}
									<p class="level-summary">{summary}</p>
								{/if}
							</div>
							{#each coursesByCourseTitle(levelGroup.courses) as courseGroup}
								{@const summary = courseGroupSummary(courseGroup.courses)}
								{@const multi = courseGroup.courses.length > 1}
								<article class="course-group">
									<h4>{courseGroup.title}</h4>
									{#if summary}
										<p class="course-group-summary">{summary}</p>
									{/if}
									{#if multi}
										<p class="course-dates-label">Course dates</p>
									{/if}
									<ul class="instance-list">
										{#each courseGroup.courses as course}
											{@const place = courseInstancePlace(course)}
											<li>
												<a href="/courses/{courseSlug(course.id)}">
													<span class="instance-date"
														>{formatDateRange(course.start_date, course.end_date)}</span
													>
													{#if place || course.medium === 'Online'}
														<span class="instance-place">
															{#if place}{place}{/if}
															{#if course.medium === 'Online'}
																{#if place}<span class="instance-sep"> · </span>{/if}
																<span class="medium-badge">Online</span>
															{/if}
														</span>
													{/if}
												</a>
											</li>
										{/each}
									</ul>
								</article>
							{/each}
						</div>
					{/each}
				</section>
			{/each}
		</div>
	</div>
</main>
