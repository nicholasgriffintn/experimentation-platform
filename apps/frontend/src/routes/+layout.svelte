<script lang="ts">
	import '../app.postcss';
	import { page } from '$app/stores';
</script>

<div class="min-h-screen bg-gray-50">
	<nav class="bg-white shadow">
		<div class="container mx-auto px-4">
			<div class="flex justify-between h-16">
				<div class="flex">
					<div class="flex-shrink-0 flex items-center">
						<a href="/" class="text-xl font-bold text-gray-800">
							ExP Platform
						</a>
					</div>

					<div class="hidden sm:ml-6 sm:flex sm:space-x-8">
						<a
							href="/"
							class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
							{$page.url.pathname === '/' ? 
								'border-blue-500 text-gray-900' : 
								'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}"
						>
							Dashboard
						</a>
						<a
							href="/experiments"
							class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
							{$page.url.pathname.startsWith('/experiments') ? 
								'border-blue-500 text-gray-900' : 
								'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}"
						>
							Experiments
						</a>
						<a
							href="/metrics"
							class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
							{$page.url.pathname.startsWith('/metrics') ? 
								'border-blue-500 text-gray-900' : 
								'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}"
						>
							Metrics
						</a>
					</div>
				</div>
			</div>
		</div>
	</nav>


	<main>
		<slot />
	</main>
</div> 