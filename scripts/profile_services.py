#!/usr/bin/env python3
"""
Performance profiling script for Smart Meeting Room services
"""
import cProfile
import pstats
import io
from datetime import datetime
import os

def profile_function(func, *args, **kwargs):
    """Profile a function and return stats"""
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    return result, s.getvalue()

def generate_profiling_report():
    """Generate profiling report for all services"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = f"profiling_reports_{timestamp}"
    os.makedirs(report_dir, exist_ok=True)
    
    print(f"Profiling reports will be saved to: {report_dir}")
    print("\nTo profile your services:")
    print("1. Start all services using docker-compose")
    print("2. Run your test suite or load tests")
    print("3. Use profiling tools like:")
    print("   - cProfile: python -m cProfile -o profile.stats your_script.py")
    print("   - memory_profiler: @profile decorator")
    print("   - line_profiler: kernprof -l -v your_script.py")
    print("\nExample profiling commands:")
    print("  # CPU profiling")
    print("  python -m cProfile -o profile.stats -m pytest services/users_service/app/tests/")
    print("\n  # Memory profiling")
    print("  python -m memory_profiler services/users_service/app/main.py")
    print("\n  # Coverage profiling")
    print("  pytest --cov=services --cov-report=html")

if __name__ == "__main__":
    generate_profiling_report()

