<script lang="ts">
	import {
		countLabel,
		courseLocation,
		courseSlug,
		coursesByLevel,
		coursesByRegion,
		formatDateRange,
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
		<nav class="contents-sidebar" aria-label="Regions">
			<h2>Jump to</h2>
			<ul>
				{#each grouped as group}
					<li>
						<a href="#{regionAnchor(group.region)}"
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
						<div
							class="contents-subsection"
							id={regionLevelAnchor(group.region, levelGroup.level)}
						>
							<h3>{levelGroup.level}</h3>
							<p class="subsection-count">{countLabel(levelGroup.courses.length, 'course')}</p>
							<ul class="course-list">
								{#each levelGroup.courses as course}
									<li>
										<a href="/courses/{courseSlug(course.id)}">{course.title}</a>
										<p>
											{formatDateRange(course.start_date, course.end_date)}
											{#if courseLocation(course)}
												· {courseLocation(course)}
											{/if}
											· {course.medium}
										</p>
									</li>
								{/each}
							</ul>
						</div>
					{/each}
				</section>
			{/each}
		</div>
	</div>
</main>
