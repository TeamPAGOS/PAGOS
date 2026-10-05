import pstats

p = pstats.Stats("temp/single_profile.prof")
p.sort_stats(pstats.SortKey.TIME)
p.print_stats(0.1)


p = pstats.Stats("temp/single_profile_fast.prof")
p.sort_stats(pstats.SortKey.TIME)
p.print_stats(0.1)
