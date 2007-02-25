import pstats

stats = pstats.Stats('profile.txt')

stats.strip_dirs()
#stats.sort_stats('calls')
stats.sort_stats('time')
#stats.sort_stats('cumulative')
stats.print_stats()
