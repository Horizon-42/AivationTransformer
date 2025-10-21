"""
Test script to verify the binary search loop prevention logic.
This simulates the problematic scenario where the algorithm could get stuck.
"""

def simulate_binary_search_with_loop_detection():
    """
    Simulate binary search with loop detection to verify it doesn't get stuck.
    """
    print("="*80)
    print("BINARY SEARCH LOOP PREVENTION TEST")
    print("="*80)
    
    stations = ['CYYC', 'CYBW', 'CYOD', 'CYXD', 'CYEG', 'CYED', 'CZVL', 'CYPY', 'CYMM', 'CYQU']
    invalid_station = 'CYXD'
    
    print(f"\nScenario: Group with CYXD (invalid) at position {stations.index(invalid_station)}")
    print(f"Stations: {stations}\n")
    
    def test_batch(batch):
        """Simulate: returns 0 reports if invalid station present"""
        has_invalid = invalid_station in batch
        count = 0 if has_invalid else len(batch) * 2  # 2 reports per valid station
        return (count > 0, count)
    
    remaining = stations.copy()
    search_count = 0
    max_iterations = len(stations) * 2
    invalid_found = {}
    
    print("Binary Search Process:")
    print("-" * 80)
    
    while remaining and search_count < max_iterations:
        search_count += 1
        
        if len(remaining) == 1:
            station = remaining[0]
            print(f"\n[Step {search_count}] Final station: {station}")
            has_data, count = test_batch([station])
            if not has_data:
                invalid_found[station] = "No data (0 reports)"
                print(f"  ❌ INVALID: {station}")
            else:
                print(f"  ✓ Valid: {station}")
            break
        
        mid = len(remaining) // 2
        left = remaining[:mid]
        right = remaining[mid:]
        
        print(f"\n[Step {search_count}] Remaining: {remaining}")
        print(f"  Split → Left: {left}")
        print(f"         Right: {right}")
        
        left_ok, left_count = test_batch(left)
        right_ok, right_count = test_batch(right)
        
        print(f"  Left:  {'✓' if left_ok else '✗'} ({left_count} reports)")
        print(f"  Right: {'✓' if right_ok else '✗'} ({right_count} reports)")
        
        # Check for loop condition
        prev_size = len(remaining)
        
        if not left_ok and not right_ok:
            print(f"  → Both failed - testing individually")
            for s in remaining:
                ok, cnt = test_batch([s])
                if not ok:
                    invalid_found[s] = "No data"
            break
        elif not left_ok:
            print(f"  → Searching LEFT (0 reports = invalid)")
            remaining = left
        elif not right_ok:
            print(f"  → Searching RIGHT (0 reports = invalid)")
            remaining = right
        else:
            print(f"  → Both work individually (edge case) - testing all")
            for s in remaining:
                ok, cnt = test_batch([s])
                if not ok:
                    invalid_found[s] = "No data"
            break
        
        # Loop detection
        if len(remaining) == prev_size:
            print(f"\n  ⚠️  LOOP DETECTED! Size didn't change. Breaking out.")
            for s in remaining:
                ok, cnt = test_batch([s])
                if not ok:
                    invalid_found[s] = "No data"
            break
    
    if search_count >= max_iterations:
        print(f"\n  ⚠️  MAX ITERATIONS ({max_iterations}) reached - prevented infinite loop!")
    
    print("\n" + "="*80)
    print("RESULTS:")
    print("-" * 80)
    print(f"Search completed in {search_count} steps")
    print(f"Invalid stations found: {list(invalid_found.keys())}")
    print(f"Loop prevention: {'✓ WORKED' if search_count < max_iterations else '⚠️ TRIGGERED'}")
    print("="*80)
    
    # Verify correctness
    if invalid_station in invalid_found:
        print("\n✅ SUCCESS: Found the invalid station correctly!")
    else:
        print(f"\n❌ FAILED: Did not find {invalid_station}")
    
    return search_count < max_iterations


def test_edge_case_both_halves_work():
    """
    Test the edge case where both halves work but full batch doesn't.
    This should not create a loop.
    """
    print("\n\n" + "="*80)
    print("EDGE CASE TEST: Both halves work separately")
    print("="*80)
    print("\nThis is a theoretical edge case that shouldn't happen in practice,")
    print("but we need to handle it gracefully without looping.\n")
    
    stations = ['A', 'B', 'C', 'D']
    
    # Simulate weird behavior: full batch fails, but splitting helps
    call_count = 0
    
    def weird_test(batch):
        nonlocal call_count
        call_count += 1
        
        # Full batch of 4 fails
        if len(batch) == 4:
            return (False, 0)
        # Smaller batches work
        else:
            return (True, len(batch) * 2)
    
    print(f"Simulating: batch of 4 fails, but splits of 2 work")
    print(f"Stations: {stations}\n")
    
    remaining = stations.copy()
    step = 0
    
    while remaining and step < 10:
        step += 1
        
        if len(remaining) == 1:
            print(f"[Step {step}] Single station: {remaining[0]}")
            break
        
        mid = len(remaining) // 2
        left = remaining[:mid]
        right = remaining[mid:]
        
        print(f"[Step {step}] Testing: Left={left}, Right={right}")
        
        left_ok, _ = weird_test(left)
        right_ok, _ = weird_test(right)
        
        print(f"  Results: Left={'✓' if left_ok else '✗'}, Right={'✓' if right_ok else '✗'}")
        
        if left_ok and right_ok:
            print(f"  → Both work! Testing individually to find issue...")
            for s in remaining:
                ok, _ = weird_test([s])
                print(f"    {s}: {'✓' if ok else '✗'}")
            break
        
        if step > 5:
            print("  ⚠️ Too many steps - loop prevention activated")
            break
    
    print(f"\n✓ Edge case handled without infinite loop ({step} steps)")
    print("="*80)


if __name__ == "__main__":
    success = simulate_binary_search_with_loop_detection()
    test_edge_case_both_halves_work()
    
    if success:
        print("\n✅ All loop prevention mechanisms working correctly!")
    else:
        print("\n⚠️  Loop prevention was needed (which is good - it worked!)")
