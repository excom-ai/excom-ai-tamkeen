"""AI Chat Service with MCP Tools using Claude - Direct Tool Calling."""

import os
import logging
import asyncio
import json
from typing import AsyncIterator, List, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

# Import MCP tools
from .mcp_tools import get_all_mcp_tools

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Disable verbose HTTP logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

# Enable Langchain debug mode for tools only
import langchain

langchain.debug = False  # Disable general debug to reduce noise


class AIService:
    """AI chat service with MCP tools using direct tool calling."""

    def __init__(self):
        """Initialize the AI service with MCP tools."""
        self.system_prompt = """You are an intelligent AI assistant with access to Tamkeen's ticketing systems.

        You have access to the following tools:
        - Query and analyze Freshservice tickets (IT service desk tickets)
        - Query and analyze JIRA demands/issues
        - Refresh data from these systems
        - Get status of cached data

        IMPORTANT SQL QUERY INSTRUCTIONS:
        - When using query_fresh_service_tickets or query_jira_demands, the data is in a dataframe called 'df'
        - Always use 'SELECT * FROM df' or 'SELECT column FROM df WHERE...' format
        - Example queries:
          - Count records: SELECT COUNT(*) FROM df
          - Filter by status: SELECT * FROM df WHERE status = 'Open'
          - Get specific columns: SELECT id, summary, status FROM df LIMIT 10
        - NEVER use just 'SELECT *' without 'FROM df'

        When users ask about tickets, issues, or demands:
        1. Use the appropriate query tool with proper SQL syntax
        2. Provide helpful insights and analysis

        Be concise, helpful, and data-driven in your responses."""

        # Initialize Claude model
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",  # Using Claude Sonnet 4
            temperature=0.2,  # Balanced temperature for reasoning
            anthropic_api_key=api_key,
            max_tokens=16384,  # Max output tokens for large responses
            max_retries=3,  # Number of retry attempts on failure
            timeout=240,  # Increased timeout to 4 minutes for complex queries
            # Additional parameters you can adjust:
            streaming=False,  # Set to True for streaming responses (faster perceived response)
            default_request_timeout=240,  # Default timeout for requests
            # top_p=0.9,  # Nucleus sampling (alternative to temperature)
            # top_k=40,  # Top-k sampling (limits vocabulary)
            # stop_sequences=[],  # Sequences that stop generation
            verbose=True,  # Disable verbose HTTP logging
        )

        # Get MCP tools and create tool map
        self.tools = get_all_mcp_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}

        # Bind tools directly to LLM (no AgentExecutor)
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
            logger.info(f"AI Service initialized with {len(self.tools)} MCP tools")
        else:
            self.llm_with_tools = self.llm
            logger.warning("AI Service initialized without tools (fallback mode)")

    async def _execute_tools_parallel(self, tool_calls: List[dict]) -> List[Any]:
        """Execute multiple tools in parallel for efficiency."""
        tasks = []
        tool_info = []  # Track tool info for logging

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_info.append({"name": tool_name, "args": tool_args})

            tool = self.tool_map.get(tool_name)
            if tool:
                # Create async task for each tool
                tasks.append(tool.ainvoke(tool_args))
            else:
                logger.warning(f"Tool {tool_name} not found")
                tasks.append(
                    asyncio.create_task(
                        self._return_error(f"Tool {tool_name} not found")
                    )
                )

        # Execute all tools in parallel
        if tasks:
            logger.info(f"\n⚡ Executing {len(tasks)} tool(s) in parallel...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log results
            for i, (result, info) in enumerate(zip(results, tool_info)):
                if isinstance(result, Exception):
                    logger.error(f"❌ Tool {info['name']} failed: {result}")
                    results[i] = str(result)
                else:
                    # Log successful result
                    result_str = str(result)
                    logger.info(f"\n✅ Tool '{info['name']}' completed:")
                    logger.info(f"   Args: {info['args']}")
                    if len(result_str) > 300:
                        logger.info(f"   Result preview: {result_str[:300]}...")
                        logger.info(f"   Result size: {len(result_str)} chars")
                    else:
                        logger.info(f"   Result: {result_str}")

            return results
        return []

    async def _return_error(self, message: str) -> str:
        """Return error message."""
        return f"Error: {message}"

    async def generate_response(
        self, message: str, conversation_history: list = None
    ) -> str:
        """Generate a response using direct tool calling."""
        try:
            # Build message list for direct tool calling
            messages = [SystemMessage(content=self.system_prompt)]

            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    if msg.get("sender") == "user":
                        messages.append(HumanMessage(content=msg.get("text", "")))
                    elif msg.get("sender") == "bot":
                        messages.append(AIMessage(content=msg.get("text", "")))

            messages.append(HumanMessage(content=message))

            # Keep calling until we get a final answer
            max_rounds = 10  # Safety limit
            total_tools_called = 0

            for round in range(max_rounds):
                # Get LLM response with tool recommendations
                logger.info(f"\n{'='*60}")
                logger.info(f"🤖 ROUND {round + 1} - Sending message to LLM")
                logger.info(f"{'='*60}")

                response = await self.llm_with_tools.ainvoke(messages)
                messages.append(response)

                # Check if LLM wants to call tools
                if hasattr(response, "tool_calls") and response.tool_calls:
                    # Execute ALL tools in parallel
                    num_tools = len(response.tool_calls)
                    total_tools_called += num_tools
                    logger.info(f"\n🔧 LLM wants to call {num_tools} tool(s):")

                    # Log tool calls requested
                    for i, tc in enumerate(response.tool_calls, 1):
                        logger.info(f"\n  Tool #{i}: {tc.get('name')}")
                        logger.info(f"  Arguments: {tc.get('args')}")
                        logger.info(f"  ID: {tc.get('id')}")

                    tool_results = await self._execute_tools_parallel(
                        response.tool_calls
                    )

                    # Add tool results as messages and log them
                    logger.info(f"\n📊 Tool results being sent back to LLM:")
                    for i, (tool_call, result) in enumerate(
                        zip(response.tool_calls, tool_results), 1
                    ):
                        result_str = str(result)
                        tool_msg = ToolMessage(
                            content=result_str,
                            tool_call_id=tool_call.get(
                                "id", f"tool_{round}_{tool_call.get('name')}"
                            ),
                        )
                        messages.append(tool_msg)

                        # Log what we're sending back
                        logger.info(f"\n  Result #{i} from {tool_call.get('name')}:")
                        if len(result_str) > 300:
                            logger.info(f"  Preview: {result_str[:300]}...")
                            logger.info(f"  (Total: {len(result_str)} chars)")
                        else:
                            logger.info(f"  Full result: {result_str}")

                    # Small delay between rounds
                    await asyncio.sleep(1.0)
                else:
                    # No more tools to call, return final response
                    logger.info(
                        f"✨ Complete after {round + 1} rounds with {total_tools_called} tool calls"
                    )
                    output = response.content
                    logger.debug(f"Final response type: {type(output)}")
                    logger.debug(
                        f"Final response: {str(output)[:500]}..."
                        if len(str(output)) > 500
                        else f"Final response: {output}"
                    )
                    break
            else:
                # Safety limit reached
                logger.warning(f"Reached max rounds ({max_rounds})")
                output = f"Analysis complete after processing {total_tools_called} operations."

            # Handle various response formats
            if isinstance(output, list):
                text_parts = []
                for item in output:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif "text" in item:
                            text_parts.append(item["text"])
                    elif isinstance(item, str):
                        text_parts.append(item)
                output = " ".join(text_parts) if text_parts else str(output)
            elif isinstance(output, dict):
                if output.get("type") == "text":
                    output = output.get("text", str(output))
                elif "text" in output:
                    output = output["text"]
                else:
                    output = str(output)

            return str(output) if output else "Query completed."

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I encountered an error: {str(e)}"

    async def stream_response(
        self, message: str, conversation_history: list = None
    ) -> AsyncIterator[str]:
        """Stream response with tool support - processes tools then streams final answer."""
        try:
            # Build message list
            messages = [SystemMessage(content=self.system_prompt)]

            if conversation_history:
                for msg in conversation_history[-10:]:
                    if msg.get("sender") == "user":
                        messages.append(HumanMessage(content=msg.get("text", "")))
                    elif msg.get("sender") == "bot":
                        messages.append(AIMessage(content=msg.get("text", "")))

            messages.append(HumanMessage(content=message))

            # Process tool calls first (non-streaming)
            max_rounds = 10
            total_tools_called = 0

            for round in range(max_rounds):
                logger.info(f"\n{'='*60}")
                logger.info(f"🤖 STREAMING - ROUND {round + 1}")
                logger.info(f"{'='*60}")

                # Skip thinking status - let natural AI response flow

                # Get initial response to check for tool calls
                response = await self.llm_with_tools.ainvoke(messages)

                # Always append the response to maintain conversation flow
                messages.append(response)

                if hasattr(response, "tool_calls") and response.tool_calls:
                    # Process tool calls
                    num_tools = len(response.tool_calls)
                    total_tools_called += num_tools

                    # Send reasoning about what we're about to do
                    tool_names = [tc.get('name') for tc in response.tool_calls]

                    # Provide contextual reasoning as normal AI response text
                    reasoning_text = ""
                    if 'get_data_status' in tool_names:
                        reasoning_text = "Let me check the current status of the cached data first...\n\n"
                    elif 'query_fresh_service_tickets' in tool_names:
                        reasoning_text = "I'll query the Freshservice tickets to get the information you need...\n\n"
                    elif 'query_jira_demands' in tool_names:
                        reasoning_text = "Let me check the JIRA demands for you...\n\n"
                    elif num_tools > 1:
                        reasoning_text = f"I need to use {num_tools} tools to get complete information...\n\n"
                    else:
                        reasoning_text = "Let me gather the information...\n\n"

                    # Stream the reasoning as normal bot content
                    for i in range(0, len(reasoning_text), 4):
                        chunk = reasoning_text[i:i+4]
                        yield json.dumps({'type': 'content', 'content': chunk})
                        await asyncio.sleep(0.015)

                    logger.info(f"\n🔧 Processing {num_tools} tool calls")

                    # Process and stream each tool individually
                    tool_results = []

                    for tc in response.tool_calls:
                        tool_name = tc.get('name')
                        tool_args = tc.get('args')
                        logger.info(f"  Tool: {tool_name} with args: {tool_args}")

                        # Create a descriptive message for each tool
                        if tool_name == 'query_fresh_service_tickets':
                            sql = tool_args.get('excomai_sql', '')
                            if 'COUNT' in sql.upper():
                                desc = "Counting Freshservice tickets"
                            elif 'WHERE' in sql.upper():
                                desc = "Filtering Freshservice tickets"
                            else:
                                desc = "Querying Freshservice tickets"
                        elif tool_name == 'query_jira_demands':
                            sql = tool_args.get('excomai_sql', '')
                            if 'COUNT' in sql.upper():
                                desc = "Counting JIRA demands"
                            elif 'WHERE' in sql.upper():
                                desc = "Filtering JIRA demands"
                            else:
                                desc = "Querying JIRA demands"
                        elif tool_name == 'get_data_status':
                            desc = "Checking data status"
                        elif tool_name == 'force_refresh_fresh_service':
                            desc = "Refreshing Freshservice data"
                        elif tool_name == 'force_refresh_jira':
                            desc = "Refreshing JIRA data"
                        else:
                            desc = f"Calling {tool_name}"

                        # Send tool execution start
                        yield json.dumps({
                            'type': 'tool_call',
                            'tool': tool_name,
                            'args': tool_args,
                            'content': f'📊 {desc}'
                        })

                        # Execute this specific tool
                        try:
                            tool_fn = self.tool_map.get(tool_name)
                            if tool_fn:
                                result = await tool_fn.ainvoke(tool_args)
                            else:
                                result = f"Tool {tool_name} not found"
                        except Exception as e:
                            result = f"Error: {str(e)}"

                        tool_results.append(result)
                        result_str = str(result)

                        # Check if result is an error
                        is_error = False
                        try:
                            result_json = json.loads(result_str) if isinstance(result_str, str) else result_str
                            if isinstance(result_json, dict) and 'error' in result_json:
                                is_error = True
                        except:
                            pass

                        # Send result immediately after execution
                        yield json.dumps({
                            'type': 'tool_result',
                            'tool': tool_name,
                            'result': result_str,  # Send full result
                            'is_error': is_error,
                            'content': f'{"❌" if is_error else "✅"} Result from {tool_name}'
                        })

                        # Small delay between tools for better UX
                        await asyncio.sleep(0.2)

                    # Send completion status for tools
                    yield json.dumps({
                        'type': 'tool_complete',
                        'content': f'Processed {num_tools} tool{"s" if num_tools > 1 else ""}'
                    })

                    # Add reasoning about what we'll do next as normal content
                    if round < max_rounds - 1:  # Not the last possible round
                        next_text = "\nAnalyzing the results...\n\n"
                        for i in range(0, len(next_text), 4):
                            chunk = next_text[i:i+4]
                            yield json.dumps({'type': 'content', 'content': chunk})
                            await asyncio.sleep(0.015)

                    # Add results to messages
                    for tool_call, result in zip(response.tool_calls, tool_results):
                        messages.append(
                            ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call.get("id", f"tool_{round}"),
                            )
                        )

                    await asyncio.sleep(0.5)
                else:
                    # No more tools - the response already has the final content
                    logger.info(
                        f"✨ Getting final response after {total_tools_called} tool calls"
                    )

                    # The current response already has the final content
                    final_content = response.content

                    logger.info(f"✨ Streaming final content: {str(final_content)[:200]}...")

                    # Now stream the final content character by character
                    if isinstance(final_content, str):
                        # Stream the text in chunks
                        chunk_size = 20  # Characters per chunk
                        for i in range(0, len(final_content), chunk_size):
                            chunk = final_content[i:i+chunk_size]
                            yield json.dumps({"type": "content", "content": chunk})
                            await asyncio.sleep(0.01)  # Small delay for streaming effect
                    else:
                        # If content is not a string, send it as is
                        yield json.dumps({"type": "content", "content": str(final_content)})

                    # Send completion signal
                    yield json.dumps({'type': 'done'})
                    break
            else:
                # Max rounds reached - get final response from LLM
                logger.warning(f"Reached max rounds with {total_tools_called} tools - getting final response")

                # Force a final response from the LLM
                final_prompt = "Based on all the data gathered, please provide your final analysis and response."
                messages.append(HumanMessage(content=final_prompt))

                try:
                    final_response = await self.llm.ainvoke(messages)
                    final_content = final_response.content if hasattr(final_response, 'content') else str(final_response)

                    # Stream the final content
                    if isinstance(final_content, str):
                        chunk_size = 20
                        for i in range(0, len(final_content), chunk_size):
                            chunk = final_content[i:i+chunk_size]
                            yield json.dumps({"type": "content", "content": chunk})
                            await asyncio.sleep(0.01)
                    else:
                        yield json.dumps({"type": "content", "content": str(final_content)})
                except Exception as e:
                    logger.error(f"Failed to get final response: {e}")
                    yield json.dumps({'type': 'content', 'content': 'Sorry, I encountered an error. Please try again.'})

                yield json.dumps({'type': 'done'})

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield json.dumps({'type': 'error', 'error': str(e)})
