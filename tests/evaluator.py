"""Evaluation framework for testing AI designs."""
import json
import os
import sys
import time
from typing import Dict, List, Any
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_interface import LocalLLM
from intent_router import IntentRouter

logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing
logger = logging.getLogger(__name__)

class Evaluator:
    """Evaluate AI design performance."""
    
    def __init__(self, design_name: str = "Design 1: Intent Router"):
        """
        Initialize evaluator.
        
        Args:
            design_name: Name of the design being evaluated
        """
        self.design_name = design_name
        self.results = {
            "design": design_name,
            "metrics": {},
            "test_results": []
        }
    
    def load_test_cases(self, filepath: str = "tests/test_cases.json") -> Dict:
        """Load test cases from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def evaluate_intent_classification(self, llm: LocalLLM, test_cases: List[Dict]) -> Dict:
        """
        Evaluate intent classification accuracy.
        
        Args:
            llm: LocalLLM instance
            test_cases: List of test cases
            
        Returns:
            Evaluation metrics
        """
        print(f"\n{'='*60}")
        print(f"Evaluating: {self.design_name}")
        print(f"Test: Intent Classification")
        print(f"{'='*60}\n")
        
        correct = 0
        total = len(test_cases)
        latencies = []
        
        for i, test_case in enumerate(test_cases, 1):
            user_input = test_case["input"]
            expected_intent = test_case["expected_intent"]
            
            # Measure latency
            start_time = time.time()
            result = llm.classify_intent(user_input)
            latency = time.time() - start_time
            latencies.append(latency)
            
            predicted_intent = result["intent"]
            is_correct = predicted_intent == expected_intent
            
            if is_correct:
                correct += 1
            
            # Print result
            status = "✓" if is_correct else "✗"
            print(f"{status} Test {i}/{total}: {test_case['description']}")
            print(f"   Input: {user_input}")
            print(f"   Expected: {expected_intent}")
            print(f"   Predicted: {predicted_intent}")
            print(f"   Latency: {latency:.3f}s\n")
            
            # Store result
            self.results["test_results"].append({
                "test_id": test_case["id"],
                "input": user_input,
                "expected_intent": expected_intent,
                "predicted_intent": predicted_intent,
                "correct": is_correct,
                "latency": latency
            })
        
        accuracy = (correct / total) * 100 if total > 0 else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        metrics = {
            "intent_accuracy": accuracy,
            "correct": correct,
            "total": total,
            "avg_latency_seconds": avg_latency,
            "min_latency_seconds": min(latencies) if latencies else 0,
            "max_latency_seconds": max(latencies) if latencies else 0
        }
        
        print(f"\n{'='*60}")
        print(f"Intent Classification Results")
        print(f"{'='*60}")
        print(f"Accuracy: {accuracy:.2f}% ({correct}/{total})")
        print(f"Average Latency: {avg_latency:.3f}s")
        print(f"Min Latency: {min(latencies):.3f}s")
        print(f"Max Latency: {max(latencies):.3f}s")
        print(f"{'='*60}\n")
        
        return metrics
    
    def evaluate_entity_extraction(self, llm: LocalLLM, test_cases: List[Dict]) -> Dict:
        """
        Evaluate entity extraction accuracy.
        
        Args:
            llm: LocalLLM instance
            test_cases: List of test cases with entities
            
        Returns:
            Evaluation metrics
        """
        print(f"\n{'='*60}")
        print(f"Test: Entity Extraction")
        print(f"{'='*60}\n")
        
        total_entities = 0
        correct_entities = 0
        
        for test_case in test_cases:
            if not test_case.get("expected_entities"):
                continue
            
            user_input = test_case["input"]
            expected_entities = test_case["expected_entities"]
            
            # Extract entities
            predicted_entities = llm.extract_entities(
                user_input,
                test_case["expected_intent"]
            )
            
            # Compare entities
            for key, expected_value in expected_entities.items():
                total_entities += 1
                predicted_value = predicted_entities.get(key)
                
                # Check if match (flexible matching)
                if predicted_value == expected_value:
                    correct_entities += 1
                    status = "✓"
                else:
                    status = "✗"
                
                print(f"{status} Entity: {key}")
                print(f"   Expected: {expected_value}")
                print(f"   Predicted: {predicted_value}\n")
        
        accuracy = (correct_entities / total_entities * 100) if total_entities > 0 else 0
        
        metrics = {
            "entity_accuracy": accuracy,
            "correct_entities": correct_entities,
            "total_entities": total_entities
        }
        
        print(f"\n{'='*60}")
        print(f"Entity Extraction Results")
        print(f"{'='*60}")
        print(f"Accuracy: {accuracy:.2f}% ({correct_entities}/{total_entities})")
        print(f"{'='*60}\n")
        
        return metrics
    
    def evaluate_booking_flow(self, router: IntentRouter, flow_tests: List[Dict]) -> Dict:
        """
        Evaluate multi-turn booking conversations.
        
        Args:
            router: IntentRouter instance
            flow_tests: List of conversation flow tests
            
        Returns:
            Evaluation metrics
        """
        print(f"\n{'='*60}")
        print(f"Test: Booking Flow")
        print(f"{'='*60}\n")
        
        completed_flows = 0
        total_flows = len(flow_tests)
        
        for flow_test in flow_tests:
            print(f"\nFlow Test {flow_test['id']}: {flow_test['description']}")
            print(f"{'-'*60}\n")
            
            conversation_state = {
                "booking": None,
                "last_intent": None,
                "last_entities": None
            }
            
            flow_success = True
            
            for turn in flow_test["conversation"]:
                user_input = turn["user"]
                expected_keywords = turn["expected_response_contains"]
                
                # Process turn
                result = router.route(user_input, conversation_state)
                conversation_state = result["state"]
                response = result["response"].lower()
                
                # Check if expected keywords present
                keywords_found = all(
                    keyword.lower() in response
                    for keyword in expected_keywords
                )
                
                status = "✓" if keywords_found else "✗"
                print(f"User: {user_input}")
                print(f"Response: {response[:100]}...")
                print(f"{status} Keywords: {expected_keywords}\n")
                
                if not keywords_found:
                    flow_success = False
            
            if flow_success:
                completed_flows += 1
                print(f"✓ Flow completed successfully\n")
            else:
                print(f"✗ Flow incomplete\n")
        
        completion_rate = (completed_flows / total_flows * 100) if total_flows > 0 else 0
        
        metrics = {
            "booking_completion_rate": completion_rate,
            "completed_flows": completed_flows,
            "total_flows": total_flows
        }
        
        print(f"\n{'='*60}")
        print(f"Booking Flow Results")
        print(f"{'='*60}")
        print(f"Completion Rate: {completion_rate:.2f}% ({completed_flows}/{total_flows})")
        print(f"{'='*60}\n")
        
        return metrics
    
    def run_full_evaluation(self, data_dir: str = "data") -> Dict:
        """
        Run complete evaluation suite.
        
        Args:
            data_dir: Directory containing data files
            
        Returns:
            Complete evaluation results
        """
        print(f"\n{'#'*60}")
        print(f"# FULL EVALUATION: {self.design_name}")
        print(f"{'#'*60}\n")
        
        # Initialize components
        print("Initializing components...\n")
        llm = LocalLLM(model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        router = IntentRouter(llm, data_dir=data_dir)
        
        # Load test cases
        test_data = self.load_test_cases()
        
        # Run evaluations
        intent_metrics = self.evaluate_intent_classification(
            llm,
            test_data["test_cases"]
        )
        
        entity_metrics = self.evaluate_entity_extraction(
            llm,
            test_data["test_cases"]
        )
        
        booking_metrics = self.evaluate_booking_flow(
            router,
            test_data["booking_flow_tests"]
        )
        
        # Combine metrics
        self.results["metrics"] = {
            **intent_metrics,
            **entity_metrics,
            **booking_metrics
        }
        
        # Save results
        self.save_results()
        
        return self.results
    
    def save_results(self, filepath: str = "tests/evaluation_results.json"):
        """Save evaluation results to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to {filepath}\n")


def main():
    """Main evaluation function."""
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "data")
    
    # Run evaluation
    evaluator = Evaluator(design_name="Design 1: Intent Router")
    results = evaluator.run_full_evaluation(data_dir=data_dir)
    
    # Print summary
    print(f"\n{'#'*60}")
    print(f"# EVALUATION SUMMARY")
    print(f"{'#'*60}")
    print(f"\nDesign: {results['design']}")
    print(f"\nKey Metrics:")
    for metric, value in results['metrics'].items():
        if isinstance(value, float):
            print(f"  {metric}: {value:.2f}")
        else:
            print(f"  {metric}: {value}")
    print(f"\n{'#'*60}\n")


if __name__ == "__main__":
    main()
