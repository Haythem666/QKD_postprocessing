"""
Profile QKD Processing Script
Analyzes performance bottlenecks in process_large_file.py
"""

import cProfile
import pstats
import sys
from pstats import SortKey


def profile_qkd_processing():
    """Run profiler on QKD processing"""
    
    # Import the processing function
    sys.path.insert(0, '.')
    from process_large_file import process_large_file
    
    # File to profile
    data_file = "raw_data/parsed_qkd_data_partial_1M.csv"  # Start with 1M for speed
    chunk_size = 1_000_000
    algorithm = "yanetal"
    
    print("="*70)
    print("  PROFILING QKD POST-PROCESSING")
    print("="*70)
    print(f"File: {data_file}")
    print(f"Chunk: {chunk_size:,}")
    print(f"Algorithm: {algorithm}")
    print("="*70)
    print("\nStarting profiler...\n")
    
    # Create profiler
    profiler = cProfile.Profile()
    
    # Run with profiling
    profiler.enable()
    process_large_file(data_file, chunk_size=chunk_size, algorithm=algorithm)
    profiler.disable()
    
    print("\n" + "="*70)
    print("  PROFILING RESULTS")
    print("="*70)
    
    # Save to file
    profiler.dump_stats('qkd_profile.prof')
    print("\n Profile saved to: qkd_profile.prof")
    
    # Print statistics
    stats = pstats.Stats(profiler)
    
    print("\n" + "="*70)
    print("  TOP 20 FUNCTIONS BY TOTAL TIME")
    print("="*70)
    stats.strip_dirs()
    stats.sort_stats(SortKey.CUMULATIVE)
    stats.print_stats(20)
    
    print("\n" + "="*70)
    print("  TOP 20 FUNCTIONS BY TIME PER CALL")
    print("="*70)
    stats.sort_stats(SortKey.TIME)
    stats.print_stats(20)
    
    print("\n" + "="*70)
    print("  FUNCTIONS CALLED MOST OFTEN")
    print("="*70)
    stats.sort_stats(SortKey.CALLS)
    stats.print_stats(20)
    
    print("\n" + "="*70)
    print("  HOW TO ANALYZE")
    print("="*70)
    print("""
Columns explained:
  ncalls  : Number of times function was called
  tottime : Total time spent in function (excluding subfunctions)
  percall : tottime / ncalls
  cumtime : Total time in function + subfunctions
  percall : cumtime / ncalls
  
To visualize (install snakeviz):
  pip install snakeviz
  snakeviz qkd_profile.prof
  
To analyze in terminal:
  python -m pstats qkd_profile.prof
  > sort cumtime
  > stats 20
""")


if __name__ == "__main__":
    profile_qkd_processing()