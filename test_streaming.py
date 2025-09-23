#!/usr/bin/env python3
"""Test streaming API endpoint"""

import asyncio
import aiohttp
import json
import time

async def test_streaming():
    url = "http://localhost:9000/api/chat/stream"

    payload = {
        "message": "Write a short story about a robot learning to paint. Make it exactly 3 sentences long.",
        "conversation_history": []
    }

    print("Testing streaming endpoint...")
    print(f"URL: {url}")
    print(f"Message: {payload['message']}")
    print("-" * 50)

    start_time = time.time()
    chunks_received = []

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            print(f"Status: {response.status}")
            print(f"Headers: {dict(response.headers)}")
            print("-" * 50)
            print("Streaming response:")
            print()

            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]
                    current_time = time.time() - start_time

                    if data == '[DONE]':
                        print(f"\n[{current_time:.2f}s] Stream complete")
                        break

                    try:
                        parsed = json.loads(data)
                        chunks_received.append({
                            'time': current_time,
                            'type': parsed.get('type'),
                            'content': parsed.get('content', '')
                        })

                        if parsed.get('type') == 'content':
                            # Print content as it arrives
                            print(parsed.get('content', ''), end='', flush=True)
                        else:
                            # Print other message types on new lines
                            print(f"\n[{current_time:.2f}s] {parsed.get('type')}: {parsed.get('content', '')}")
                    except json.JSONDecodeError as e:
                        print(f"\n[{current_time:.2f}s] Failed to parse: {data[:100]}")

    print("\n" + "-" * 50)
    print(f"Total time: {time.time() - start_time:.2f} seconds")
    print(f"Total chunks received: {len(chunks_received)}")

    # Analyze chunk timing
    if chunks_received:
        content_chunks = [c for c in chunks_received if c['type'] == 'content']
        print(f"Content chunks: {len(content_chunks)}")

        if len(content_chunks) > 1:
            delays = []
            for i in range(1, len(content_chunks)):
                delay = content_chunks[i]['time'] - content_chunks[i-1]['time']
                delays.append(delay)

            if delays:
                avg_delay = sum(delays) / len(delays)
                max_delay = max(delays)
                min_delay = min(delays)
                print(f"Chunk delays - Avg: {avg_delay:.3f}s, Min: {min_delay:.3f}s, Max: {max_delay:.3f}s")

                # Check if it's truly streaming
                if avg_delay < 0.1:
                    print("✅ TRUE STREAMING DETECTED (chunks arriving quickly)")
                elif avg_delay < 1.0:
                    print("⚠️ PARTIAL STREAMING (some buffering detected)")
                else:
                    print("❌ NOT STREAMING (large delays between chunks)")

if __name__ == "__main__":
    asyncio.run(test_streaming())