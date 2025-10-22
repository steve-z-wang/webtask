"""
Example demonstrating the new execute_step method for step-by-step task execution.

This shows how to use execute_step for better visibility into the agent's
decision-making process, allowing you to inspect each step before proceeding.
"""

from webtask import Webtask
from webtask.integrations.llm import GeminiLLM


async def main():
    # Create Webtask manager and agent
    wt = Webtask()
    llm = GeminiLLM.create(model="gemini-2.5-flash", temperature=0.3)
    agent = await wt.create_agent(llm=llm)
    
    # Define the task
    task = "search for cats and click the first result"
    
    # Execute step by step with visibility
    max_steps = 10
    for i in range(max_steps):
        print(f"\n{'='*60}")
        print(f"STEP {i+1}")
        print(f"{'='*60}")
        
        # Execute one step
        step = await agent.execute_step(task)
        
        # Show what the agent did
        print(f"\nActions taken:")
        for j, (action, execution) in enumerate(zip(step.proposals, step.executions), 1):
            print(f"  {j}. {action.tool_name}: {action.reason}")
            print(f"     Parameters: {action.parameters}")
            print(f"     Status: {'✓ Success' if execution.success else '✗ Failed'}")
            if execution.error:
                print(f"     Error: {execution.error}")
        
        # Show verification result
        print(f"\nVerification:")
        print(f"  Complete: {step.verification.complete}")
        print(f"  Message: {step.verification.message}")
        
        # Check if task is complete
        if step.verification.complete:
            print(f"\n✅ Task completed after {i+1} steps!")
            break
    else:
        print(f"\n⚠️ Task not completed after {max_steps} steps")
    
    # Show full history
    print(f"\n{'='*60}")
    print("FULL STEP HISTORY")
    print(f"{'='*60}")
    all_steps = agent.step_history.get_all()
    print(f"Total steps: {len(all_steps)}")
    
    # Cleanup
    await agent.close()


# Alternative: Compare with the original execute method
async def compare_methods():
    """
    Demonstrates the difference between execute and execute_step.
    
    execute():      Runs the whole task automatically until completion
    execute_step(): Runs one step at a time for better visibility
    """
    wt = Webtask()
    llm = GeminiLLM.create(model="gemini-2.5-flash", temperature=0.3)
    agent = await wt.create_agent(llm=llm)
    
    # Method 1: Execute all at once (original behavior)
    print("Method 1: Using execute() - runs until completion")
    result = await agent.execute("search for cats", max_steps=10)
    print(f"Completed: {result.completed}")
    print(f"Steps taken: {len(result.steps)}")
    print(f"Final message: {result.message}")
    
    # Clear history for method 2
    agent.step_history.clear()
    
    # Method 2: Execute step by step (new behavior)
    print("\nMethod 2: Using execute_step() - manual control")
    for i in range(10):
        step = await agent.execute_step("search for cats")
        print(f"Step {i+1}: {step.verification.message}")
        if step.verification.complete:
            print(f"Task complete!")
            break
    
    await agent.close()


if __name__ == "__main__":
    import asyncio
    
    # Run the step-by-step example
    asyncio.run(main())
    
    # Uncomment to see the comparison
    # asyncio.run(compare_methods())
