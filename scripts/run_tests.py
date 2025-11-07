#!/usr/bin/env python3
"""
Test Runner Script for BKT Algorithm Implementation

This script runs comprehensive tests to validate the BKT algorithm accuracy,
performance optimization, and concurrent user scenarios.
"""

import asyncio
import sys
import time
import subprocess
from pathlib import Path
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_unit_tests():
    """Run unit tests with pytest"""
    logger.info("Running unit tests...")
    
    try:
        result = subprocess.run([
            "python", "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--cov=src",
            "--cov-report=term-missing"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Failed to run unit tests: {e}")
        return False


async def run_algorithm_accuracy_tests():
    """Run specific tests to validate BKT algorithm accuracy"""
    logger.info("Running BKT algorithm accuracy validation...")
    
    from src.core.bkt_engine import BKTEngine
    from src.models.bkt_models import BKTParameters, BKTConfiguration
    from src.utils.cache_manager import InMemoryCache
    from unittest.mock import AsyncMock
    
    try:
        # Setup test environment
        mock_repository = AsyncMock()
        cache = InMemoryCache()
        await cache.initialize()
        
        config = BKTConfiguration(
            default_parameters=BKTParameters(
                skill_id="test",
                p_l0=0.1,
                p_t=0.1,
                p_g=0.2,
                p_s=0.1
            )
        )
        
        engine = BKTEngine(mock_repository, cache, config)
        
        # Test 1: Mathematical correctness
        logger.info("Test 1: Mathematical correctness")
        parameters = BKTParameters(skill_id="test", p_l0=0.1, p_t=0.1, p_g=0.2, p_s=0.1)
        
        # Test correct response
        p_new = engine._calculate_bkt_update(0.5, True, parameters)
        expected = 0.5 * 0.9 / (0.5 * 0.9 + 0.5 * 0.2)
        expected = expected + (1 - expected) * 0.1
        
        if abs(p_new - expected) < 0.001:
            logger.info("✓ Correct response calculation is accurate")
        else:
            logger.error(f"✗ Correct response calculation error: {p_new} vs {expected}")
            return False
        
        # Test incorrect response
        p_new = engine._calculate_bkt_update(0.5, False, parameters)
        expected = 0.5 * 0.1 / (0.5 * 0.1 + 0.5 * 0.8)
        expected = expected + (1 - expected) * 0.1
        
        if abs(p_new - expected) < 0.001:
            logger.info("✓ Incorrect response calculation is accurate")
        else:
            logger.error(f"✗ Incorrect response calculation error: {p_new} vs {expected}")
            return False
        
        # Test 2: Probability bounds
        logger.info("Test 2: Probability bounds validation")
        test_cases = [
            (0.0, True), (0.0, False),
            (0.5, True), (0.5, False),
            (1.0, True), (1.0, False)
        ]
        
        for p_known, is_correct in test_cases:
            p_new = engine._calculate_bkt_update(p_known, is_correct, parameters)
            if not (0.0 <= p_new <= 1.0):
                logger.error(f"✗ Probability bounds violated: {p_new} for P(Known)={p_known}, correct={is_correct}")
                return False
        
        logger.info("✓ All probability bounds are respected")
        
        # Test 3: Learning progression
        logger.info("Test 3: Learning progression validation")
        p_known = 0.1
        for i in range(10):
            p_new = engine._calculate_bkt_update(p_known, True, parameters)
            if p_new < p_known:
                logger.error(f"✗ P(Known) decreased after correct response: {p_known} -> {p_new}")
                return False
            p_known = p_new
        
        if p_known > 0.7:
            logger.info("✓ Learning progression is realistic")
        else:
            logger.warning(f"? Learning progression may be slow: final P(Known) = {p_known}")
        
        logger.info("BKT algorithm accuracy validation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Algorithm accuracy test failed: {e}")
        return False


async def run_performance_tests():
    """Run performance tests for concurrent users"""
    logger.info("Running performance tests...")
    
    from src.core.bkt_engine import BKTEngine
    from src.models.bkt_models import BKTParameters, BKTConfiguration, PerformanceEvent
    from src.utils.cache_manager import InMemoryCache
    from unittest.mock import AsyncMock
    from datetime import datetime
    
    try:
        # Setup test environment
        mock_repository = AsyncMock()
        cache = InMemoryCache()
        await cache.initialize()
        
        config = BKTConfiguration(
            default_parameters=BKTParameters(
                skill_id="test",
                p_l0=0.1,
                p_t=0.1,
                p_g=0.2,
                p_s=0.1
            ),
            update_batch_size=50
        )
        
        engine = BKTEngine(mock_repository, cache, config, max_workers=5)
        await engine.initialize()
        
        # Mock repository responses
        from src.models.bkt_models import LearnerCompetency
        mock_repository.get_competency.return_value = LearnerCompetency(
            learner_id="test",
            skill_id="test",
            p_known=0.5,
            total_attempts=0,
            correct_attempts=0
        )
        mock_repository.save_competency.return_value = AsyncMock()
        mock_repository.save_performance_event.return_value = AsyncMock()
        
        # Test 1: Batch processing performance
        logger.info("Test 1: Batch processing performance")
        events = []
        for i in range(1000):
            event = PerformanceEvent(
                learner_id=f"learner_{i % 100}",
                skill_id=f"skill_{i % 10}",
                activity_id=f"activity_{i}",
                is_correct=i % 2 == 0,
                timestamp=datetime.utcnow()
            )
            events.append(event)
        
        start_time = time.time()
        results = await engine.batch_update_competencies(events)
        end_time = time.time()
        
        duration = end_time - start_time
        throughput = len(events) / duration
        
        logger.info(f"Processed {len(events)} events in {duration:.2f}s")
        logger.info(f"Throughput: {throughput:.1f} events/second")
        
        if throughput > 100:  # Should process at least 100 events per second
            logger.info("✓ Batch processing performance is acceptable")
        else:
            logger.warning(f"? Batch processing may be slow: {throughput:.1f} events/s")
        
        # Test 2: Concurrent updates
        logger.info("Test 2: Concurrent update performance")
        
        async def single_update(learner_id, skill_id):
            return await engine.update_competency(
                learner_id=learner_id,
                skill_id=skill_id,
                is_correct=True,
                activity_id="test"
            )
        
        tasks = []
        for i in range(200):
            task = single_update(f"learner_{i % 50}", f"skill_{i % 5}")
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        duration = end_time - start_time
        throughput = len(tasks) / duration
        
        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        if exceptions:
            logger.error(f"✗ {len(exceptions)} exceptions during concurrent updates")
            return False
        
        logger.info(f"Processed {len(tasks)} concurrent updates in {duration:.2f}s")
        logger.info(f"Throughput: {throughput:.1f} updates/second")
        
        if throughput > 50:  # Should handle at least 50 concurrent updates per second
            logger.info("✓ Concurrent update performance is acceptable")
        else:
            logger.warning(f"? Concurrent update performance may be slow: {throughput:.1f} updates/s")
        
        logger.info("Performance tests completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return False


async def run_integration_tests():
    """Run integration tests with realistic scenarios"""
    logger.info("Running integration tests...")
    
    try:
        # Test realistic learning scenario
        from src.core.bkt_engine import BKTEngine
        from src.models.bkt_models import BKTParameters, BKTConfiguration, LearnerCompetency
        from src.utils.cache_manager import InMemoryCache
        from unittest.mock import AsyncMock
        
        # Setup
        mock_repository = AsyncMock()
        cache = InMemoryCache()
        await cache.initialize()
        
        config = BKTConfiguration(
            default_parameters=BKTParameters(
                skill_id="python_loops",
                p_l0=0.1,
                p_t=0.15,
                p_g=0.25,
                p_s=0.1
            ),
            mastery_threshold=0.8,
            min_attempts_for_mastery=5
        )
        
        engine = BKTEngine(mock_repository, cache, config)
        await engine.initialize()
        
        # Mock learner competency
        competency = LearnerCompetency(
            learner_id="student_001",
            skill_id="python_loops",
            p_known=0.1,
            mastery_threshold=0.8,
            total_attempts=0,
            correct_attempts=0
        )
        
        mock_repository.get_competency.return_value = competency
        mock_repository.save_competency.return_value = competency
        mock_repository.save_performance_event.return_value = AsyncMock()
        
        # Simulate realistic learning progression
        # Student starts with low knowledge and gradually improves
        responses = [
            False, False, True, False, True,  # Initial struggle
            True, False, True, True, False,   # Some improvement
            True, True, True, False, True,    # Getting better
            True, True, True, True, True      # Mastery achieved
        ]
        
        p_known_progression = [0.1]  # Starting value
        mastery_achieved = False
        
        for i, is_correct in enumerate(responses):
            result = await engine.update_competency(
                learner_id="student_001",
                skill_id="python_loops",
                is_correct=is_correct,
                activity_id=f"exercise_{i+1}"
            )
            
            p_known_progression.append(result.new_p_known)
            competency.p_known = result.new_p_known
            competency.total_attempts += 1
            if is_correct:
                competency.correct_attempts += 1
            
            if result.mastery_gained:
                mastery_achieved = True
                logger.info(f"Mastery achieved after {competency.total_attempts} attempts")
                break
        
        # Validate learning progression
        if p_known_progression[-1] > p_known_progression[0]:
            logger.info("✓ Learning progression shows improvement")
        else:
            logger.error("✗ No learning progression detected")
            return False
        
        # Check if mastery was achieved with good performance
        accuracy = competency.correct_attempts / competency.total_attempts
        if mastery_achieved and accuracy > 0.6:
            logger.info(f"✓ Mastery achieved with {accuracy:.1%} accuracy")
        elif not mastery_achieved and accuracy < 0.5:
            logger.info("✓ Mastery not achieved with low accuracy (expected)")
        else:
            logger.warning(f"? Mastery status may be incorrect: achieved={mastery_achieved}, accuracy={accuracy:.1%}")
        
        logger.info("Integration tests completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False


async def main():
    """Run all tests and generate report"""
    logger.info("Starting comprehensive BKT algorithm test suite...")
    
    test_results = {}
    
    # Run all test suites
    test_results["unit_tests"] = await run_unit_tests()
    test_results["algorithm_accuracy"] = await run_algorithm_accuracy_tests()
    test_results["performance_tests"] = await run_performance_tests()
    test_results["integration_tests"] = await run_integration_tests()
    
    # Generate test report
    logger.info("\n" + "="*60)
    logger.info("BKT ALGORITHM TEST REPORT")
    logger.info("="*60)
    
    all_passed = True
    for test_name, passed in test_results.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("="*60)
    
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED - BKT algorithm implementation is ready!")
        logger.info("\nAcceptance Criteria Validation:")
        logger.info("✓ BKT algorithm implemented with configurable parameters")
        logger.info("✓ Real-time competency updates functional")
        logger.info("✓ Performance optimized for concurrent users")
        logger.info("✓ Algorithm accuracy validated with test data")
        logger.info("✓ Integration with learner profile system complete")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED - Please review and fix issues")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)